"""Main client for Gemini CLI SDK."""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
from .models import GeminiResponse, GeminiConfig, SessionInfo, MessageRole
from .session import SessionManager
from .process_manager import ProcessManager
from .config import ConfigManager
from .system_commands import SystemCommands
from .exceptions import GeminiSDKError, GeminiValidationError


class GeminiClient:
    """Main client for interacting with Gemini CLI."""
    
    def __init__(self, config: Optional[GeminiConfig] = None, 
                 config_file: Optional[str] = None):
        """Initialize Gemini client.
        
        Args:
            config: Optional configuration object
            config_file: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_file)
        self.config = config or self.config_manager.load_config()
        self.session_manager = SessionManager(self.config.max_context_length)
        self.process_manager = ProcessManager(self.config)
        self.system_commands = SystemCommands(self.process_manager, self.config)
        self._started = False
        self._logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the client and initialize resources."""
        if not self._started:
            await self.process_manager.start()
            self._started = True
            self._logger.info("Gemini client started")
    
    async def stop(self):
        """Stop the client and clean up resources."""
        if self._started:
            await self.process_manager.stop()
            self._started = False
            self._logger.info("Gemini client stopped")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    # Session Management Methods
    
    def create_session(self, user_id: Optional[str] = None, 
                      metadata: Optional[Dict] = None) -> str:
        """Create a new conversation session.
        
        Args:
            user_id: Optional user identifier
            metadata: Optional metadata to associate with session
            
        Returns:
            str: Unique session ID
        """
        session_id = self.session_manager.create_session(user_id, metadata)
        self._logger.info(f"Created session: {session_id}")
        return session_id
    
    def close_session(self, session_id: str):
        """Close a conversation session.
        
        Args:
            session_id: Session ID to close
        """
        if not self.session_manager.session_exists(session_id):
            self._logger.warning(f"Attempted to close non-existent session: {session_id}")
            return
        
        # Close associated process if any (only if event loop is running)
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.process_manager.close_session_process(session_id))
        except RuntimeError:
            # No running event loop, skip async cleanup
            pass
        
        # Close session
        self.session_manager.close_session(session_id)
        self._logger.info(f"Closed session: {session_id}")
    
    def get_session_info(self, session_id: str) -> SessionInfo:
        """Get information about a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionInfo: Session information
        """
        return self.session_manager.get_session_info(session_id)
    
    def list_sessions(self) -> List[SessionInfo]:
        """List all active sessions.
        
        Returns:
            List[SessionInfo]: List of session information
        """
        return self.session_manager.list_sessions()
    
    def clear_session_context(self, session_id: str):
        """Clear the conversation context for a session.
        
        Args:
            session_id: Session ID
        """
        self.session_manager.clear_session_messages(session_id)
        self._logger.info(f"Cleared context for session: {session_id}")
    
    # Message Sending Methods
    
    async def send_message(self, message: str, session_id: Optional[str] = None,
                          system_instruction: Optional[str] = None,
                          maintain_context: bool = True,
                          stream: bool = False) -> Union[GeminiResponse, AsyncGenerator[str, None]]:
        """Send a message to Gemini.
        
        Args:
            message: Message content to send
            session_id: Optional session ID for context
            system_instruction: Optional system instruction
            maintain_context: Whether to maintain conversation context
            stream: If True, returns an async generator for streaming output.
            
        Returns:
            GeminiResponse or AsyncGenerator: Response from Gemini or a stream.
            
        Raises:
            GeminiSDKError: If sending fails
            GeminiValidationError: If input validation fails
        """
        # Validate inputs
        if not message or not message.strip():
            raise GeminiValidationError("Message cannot be empty")
        
        if session_id and not self.session_manager.session_exists(session_id):
            raise GeminiValidationError(f"Session {session_id} does not exist")
        
        # Ensure client is started
        if not self._started:
            await self.start()
        
        context = None
        if maintain_context and session_id:
            context = self.session_manager.get_context(session_id)
        
        process = await self.process_manager.get_or_create_process(session_id)
            
        full_message = message
        if system_instruction:
            full_message = f"System: {system_instruction}\n\nUser: {message}"
        
        if not stream:
            response_content = await self.process_manager.send_message(
                process, full_message, context, stream=False
            )
            
            if maintain_context and session_id:
                self.session_manager.add_message(session_id, MessageRole.USER, message)
                self.session_manager.add_message(session_id, MessageRole.ASSISTANT, response_content)
            
            return GeminiResponse(
                content=response_content,
                session_id=session_id,
                process_id=process.process_id
            )
        else:
            async def stream_generator() -> AsyncGenerator[str, None]:
                response_chunks = []
                stream_response = await self.process_manager.send_message(
                    process, full_message, context, stream=True
                )
                
                async for chunk in stream_response:
                    response_chunks.append(chunk)
                    yield chunk
                
                if maintain_context and session_id:
                    full_response = "".join(response_chunks)
                    self.session_manager.add_message(session_id, MessageRole.USER, message)
                    self.session_manager.add_message(session_id, MessageRole.ASSISTANT, full_response)
                    self._logger.debug(f"Stream finished. Updated context for session {session_id}")

            return stream_generator()
    
    async def chat(self, message: str, session_id: Optional[str] = None,
                   stream: bool = False) -> Union[GeminiResponse, AsyncGenerator[str, None]]:
        """Simple chat interface.
        
        Args:
            message: Message to send
            session_id: Optional session ID for context
            stream: If True, returns an async generator for streaming output.
            
        Returns:
            GeminiResponse or AsyncGenerator: Response from Gemini or a stream.
        """
        return await self.send_message(message, session_id, stream=stream)
    
    async def one_shot(self, message: str, system_instruction: Optional[str] = None,
                       stream: bool = False) -> Union[GeminiResponse, AsyncGenerator[str, None]]:
        """Send a one-time message without maintaining context.
        
        Args:
            message: Message to send
            system_instruction: Optional system instruction
            stream: If True, returns an async generator for streaming output.
            
        Returns:
            GeminiResponse or AsyncGenerator: Response from Gemini or a stream.
        """
        return await self.send_message(
            message, 
            system_instruction=system_instruction,
            maintain_context=False,
            stream=stream
        )
    
    # Batch Operations
    
    async def send_batch(self, messages: List[str], session_id: Optional[str] = None,
                        system_instruction: Optional[str] = None) -> List[GeminiResponse]:
        """Send multiple messages in sequence.
        
        Args:
            messages: List of messages to send
            session_id: Optional session ID for context
            system_instruction: Optional system instruction for all messages
            
        Returns:
            List[GeminiResponse]: List of responses
        """
        if not messages:
            raise GeminiValidationError("Messages list cannot be empty")
        
        responses = []
        for message in messages:
            response = await self.send_message(
                message, 
                session_id=session_id,
                system_instruction=system_instruction
            )
            responses.append(response)
        
        self._logger.info(f"Sent batch of {len(messages)} messages")
        return responses
    
    async def send_concurrent(self, messages: List[str], 
                             system_instruction: Optional[str] = None) -> List[GeminiResponse]:
        """Send multiple messages concurrently (without shared context).
        
        Args:
            messages: List of messages to send
            system_instruction: Optional system instruction for all messages
            
        Returns:
            List[GeminiResponse]: List of responses
        """
        if not messages:
            raise GeminiValidationError("Messages list cannot be empty")
        
        # Create tasks for concurrent execution
        tasks = [
            self.send_message(
                message,
                system_instruction=system_instruction,
                maintain_context=False
            )
            for message in messages
        ]
        
        responses = await asyncio.gather(*tasks)
        self._logger.info(f"Sent {len(messages)} messages concurrently")
        return responses
    
    # Utility Methods
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics.
        
        Returns:
            Dict: Statistics about the client state
        """
        return {
            'started': self._started,
            'sessions': {
                'total': self.session_manager.get_session_count(),
                'active': len([s for s in self.session_manager.list_sessions() 
                              if s.message_count > 0])
            },
            'processes': {
                'total': self.process_manager.get_process_count(),
                'idle': self.process_manager.get_idle_process_count(),
                'max': self.config.max_processes
            },
            'config': {
                'max_processes': self.config.max_processes,
                'idle_timeout': self.config.idle_timeout,
                'max_context_length': self.config.max_context_length,
                'response_timeout': self.config.response_timeout
            }
        }
    
    def cleanup_inactive_sessions(self, timeout: int = 3600):
        """Clean up inactive sessions.
        
        Args:
            timeout: Inactivity timeout in seconds
        """
        self.session_manager.cleanup_inactive_sessions(timeout)
        self._logger.info("Cleaned up inactive sessions")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the client.
        
        Returns:
            Dict: Health check results
        """
        try:
            # Test basic functionality
            test_response = await self.one_shot("Hello")
            
            return {
                'status': 'healthy',
                'gemini_responsive': bool(test_response),
                'stats': self.get_stats()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'stats': self.get_stats()
            }
    
    # Configuration Methods
    
    def update_config(self, **kwargs):
        """Update configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        # Update config object
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise GeminiValidationError(f"Unknown configuration parameter: {key}")
        
        # Save updated config
        self.config_manager.save_config(self.config)
        self._logger.info(f"Updated configuration: {kwargs}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Dict: Current configuration
        """
        return {
            'max_processes': self.config.max_processes,
            'idle_timeout': self.config.idle_timeout,
            'max_context_length': self.config.max_context_length,
            'gemini_command': self.config.gemini_command,
            'gemini_args': self.config.gemini_args,
            'enable_logging': self.config.enable_logging,
            'log_level': self.config.log_level,
            'response_timeout': self.config.response_timeout,
            'cleanup_interval': self.config.cleanup_interval
        }
    
    # System Commands Methods
    
    async def execute_system_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute a Gemini CLI system command.
        
        Args:
            command: System command name (with or without leading /)
            args: Optional command arguments
            
        Returns:
            Dict: Command execution result
            
        Raises:
            GeminiValidationError: If command is invalid
            GeminiSDKError: If execution fails
        """
        return await self.system_commands.execute_command(command, args)
    
    async def system_help(self) -> Dict[str, Any]:
        """Get help information for system commands.
        
        Returns:
            Dict: Help information
        """
        return await self.execute_system_command('help')
    
    async def system_about(self) -> Dict[str, Any]:
        """Get version and about information.
        
        Returns:
            Dict: Version information
        """
        return await self.execute_system_command('about')
    
    async def system_clear(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Clear screen and conversation history.
        
        Args:
            session_id: Optional session ID to clear
            
        Returns:
            Dict: Clear operation result
        """
        if session_id:
            self.clear_session_context(session_id)
        return await self.execute_system_command('clear')
    
    async def system_stats(self, stat_type: str = 'general') -> Dict[str, Any]:
        """Get system statistics.
        
        Args:
            stat_type: Type of statistics ('general', 'model', 'tools')
            
        Returns:
            Dict: Statistics information
        """
        args = [stat_type] if stat_type != 'general' else []
        return await self.execute_system_command('stats', args)
    
    async def chat_save_checkpoint(self, tag: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Save current conversation as a checkpoint.
        
        Args:
            tag: Checkpoint tag/name
            session_id: Optional session ID
            
        Returns:
            Dict: Save operation result
        """
        # TODO: Integrate with actual session data
        return await self.execute_system_command('chat', ['save', tag])
    
    async def chat_resume_checkpoint(self, tag: str) -> Dict[str, Any]:
        """Resume conversation from a checkpoint.
        
        Args:
            tag: Checkpoint tag/name
            
        Returns:
            Dict: Resume operation result
        """
        return await self.execute_system_command('chat', ['resume', tag])
    
    async def chat_list_checkpoints(self) -> Dict[str, Any]:
        """List saved conversation checkpoints.
        
        Returns:
            Dict: List of checkpoints
        """
        return await self.execute_system_command('chat', ['list'])
    
    async def chat_delete_checkpoint(self, tag: str) -> Dict[str, Any]:
        """Delete a conversation checkpoint.
        
        Args:
            tag: Checkpoint tag/name
            
        Returns:
            Dict: Delete operation result
        """
        return await self.execute_system_command('chat', ['delete', tag])
    
    async def chat_share(self, filename: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Share conversation to a file.
        
        Args:
            filename: Output filename
            session_id: Optional session ID
            
        Returns:
            Dict: Share operation result
        """
        # TODO: Integrate with actual session data
        return await self.execute_system_command('chat', ['share', filename])
    
    async def manage_extensions(self, action: str, *args) -> Dict[str, Any]:
        """Manage Gemini CLI extensions.
        
        Args:
            action: Extension action ('list', 'update', 'explore')
            *args: Additional arguments for the action
            
        Returns:
            Dict: Extension management result
        """
        return await self.execute_system_command('extensions', [action] + list(args))
    
    async def manage_mcp_servers(self, action: str, *args) -> Dict[str, Any]:
        """Manage MCP servers.
        
        Args:
            action: MCP action ('list', 'desc', 'schema', 'auth', 'refresh')
            *args: Additional arguments for the action
            
        Returns:
            Dict: MCP management result
        """
        return await self.execute_system_command('mcp', [action] + list(args))
    
    async def manage_workspace_directories(self, action: str, *paths) -> Dict[str, Any]:
        """Manage workspace directories.
        
        Args:
            action: Directory action ('add', 'show')
            *paths: Directory paths (for 'add' action)
            
        Returns:
            Dict: Directory management result
        """
        return await self.execute_system_command('directory', [action] + list(paths))
    
    async def manage_memory(self, action: str, content: str = None) -> Dict[str, Any]:
        """Manage memory system.
        
        Args:
            action: Memory action ('show', 'add', 'refresh', 'list')
            content: Content to add (for 'add' action)
            
        Returns:
            Dict: Memory management result
        """
        args = [action]
        if content and action == 'add':
            args.append(content)
        return await self.execute_system_command('memory', args)
    
    async def list_tools(self, show_descriptions: bool = False) -> Dict[str, Any]:
        """List available Gemini CLI tools.
        
        Args:
            show_descriptions: Whether to show tool descriptions
            
        Returns:
            Dict: Tools list
        """
        args = ['desc'] if show_descriptions else []
        return await self.execute_system_command('tools', args)
    
    # File Reference and Shell Command Support
    
    def process_file_references(self, message: str) -> str:
        """Process @ file references in message.
        
        Args:
            message: Message with potential @ file references
            
        Returns:
            str: Processed message with file contents
        """
        import re
        import os
        
        # Pattern to match @filename or @"filename with spaces"
        pattern = r'@(?:"([^"]+)"|([^\s]+))'
        
        def replace_file_ref(match):
            # Get filename from either quoted or unquoted group
            filename = match.group(1) if match.group(1) else match.group(2)
            
            try:
                # Handle relative paths
                if not os.path.isabs(filename):
                    # Try current working directory first
                    if os.path.exists(filename):
                        filepath = filename
                    else:
                        # Try relative to user's home directory
                        home_path = os.path.expanduser(f"~/{filename}")
                        if os.path.exists(home_path):
                            filepath = home_path
                        else:
                            return f"[File not found: {filename}]"
                else:
                    filepath = filename
                
                # Check if file exists and is readable
                if not os.path.exists(filepath):
                    return f"[File not found: {filename}]"
                
                if not os.path.isfile(filepath):
                    return f"[Not a file: {filename}]"
                
                # Read file content with encoding detection
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try with different encodings
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            with open(filepath, 'r', encoding=encoding) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        return f"[Cannot read file (encoding issue): {filename}]"
                
                # Limit file size to prevent overwhelming the context
                max_size = 10000  # 10KB limit
                if len(content) > max_size:
                    content = content[:max_size] + f"\n... [File truncated, showing first {max_size} characters]"
                
                # Format the file content nicely
                return f"\n--- Content of {filename} ---\n{content}\n--- End of {filename} ---\n"
                
            except PermissionError:
                return f"[Permission denied: {filename}]"
            except Exception as e:
                self._logger.error(f"Error reading file {filename}: {e}")
                return f"[Error reading file {filename}: {str(e)}]"
        
        # Replace all file references in the message
        processed_message = re.sub(pattern, replace_file_ref, message)
        
        # Log if any file references were processed
        if processed_message != message:
            self._logger.debug("Processed file references in message")
        
        return processed_message
    
    async def execute_shell_command(self, command: str) -> Dict[str, Any]:
        """Execute a shell command (! syntax).
        
        Args:
            command: Shell command to execute
            
        Returns:
            Dict: Command execution result
        """
        import subprocess
        import shlex
        import os
        
        # Security: List of allowed commands (whitelist approach)
        allowed_commands = {
            'ls', 'dir', 'pwd', 'whoami', 'date', 'echo', 'cat', 'head', 'tail',
            'grep', 'find', 'wc', 'sort', 'uniq', 'which', 'where', 'type',
            'ps', 'top', 'df', 'du', 'free', 'uptime', 'uname', 'hostname',
            'git', 'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn',
            'curl', 'wget', 'ping', 'nslookup', 'dig'
        }
        
        # Dangerous commands to block
        dangerous_commands = {
            'rm', 'del', 'rmdir', 'rd', 'format', 'fdisk', 'mkfs',
            'sudo', 'su', 'chmod', 'chown', 'passwd', 'useradd', 'userdel',
            'kill', 'killall', 'pkill', 'shutdown', 'reboot', 'halt',
            'dd', 'mount', 'umount', 'crontab', 'at', 'batch'
        }
        
        try:
            # Parse command safely
            command_parts = shlex.split(command.strip())
            if not command_parts:
                return {
                    'command': command,
                    'stdout': '',
                    'stderr': 'Empty command',
                    'return_code': 1,
                    'success': False,
                    'message': 'Empty command provided'
                }
            
            base_command = command_parts[0].lower()
            
            # Check for dangerous commands
            if base_command in dangerous_commands:
                return {
                    'command': command,
                    'stdout': '',
                    'stderr': f'Command "{base_command}" is not allowed for security reasons',
                    'return_code': 1,
                    'success': False,
                    'message': f'Dangerous command "{base_command}" blocked'
                }
            
            # Check if command is in allowed list (optional - can be disabled for more flexibility)
            # Uncomment the following lines for stricter security:
            # if base_command not in allowed_commands:
            #     return {
            #         'command': command,
            #         'stdout': '',
            #         'stderr': f'Command "{base_command}" is not in the allowed list',
            #         'return_code': 1,
            #         'success': False,
            #         'message': f'Command "{base_command}" not allowed'
            #     }
            
            # Set timeout and limits
            timeout = 30  # 30 seconds timeout
            max_output_size = 10000  # 10KB output limit
            
            # Execute command with security measures
            process = await asyncio.create_subprocess_exec(
                *command_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
                env=dict(os.environ),  # Use current environment
                limit=max_output_size
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                # Decode output
                stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ''
                stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ''
                
                # Limit output size
                if len(stdout_text) > max_output_size:
                    stdout_text = stdout_text[:max_output_size] + f"\n... [Output truncated at {max_output_size} characters]"
                
                if len(stderr_text) > max_output_size:
                    stderr_text = stderr_text[:max_output_size] + f"\n... [Error output truncated at {max_output_size} characters]"
                
                success = process.returncode == 0
                
                result = {
                    'command': command,
                    'stdout': stdout_text,
                    'stderr': stderr_text,
                    'return_code': process.returncode,
                    'success': success,
                    'message': 'Command executed successfully' if success else f'Command failed with return code {process.returncode}'
                }
                
                self._logger.info(f"Executed shell command: {command} (return code: {process.returncode})")
                return result
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                
                return {
                    'command': command,
                    'stdout': '',
                    'stderr': f'Command timed out after {timeout} seconds',
                    'return_code': -1,
                    'success': False,
                    'message': f'Command timed out after {timeout} seconds'
                }
                
        except FileNotFoundError:
            return {
                'command': command,
                'stdout': '',
                'stderr': f'Command not found: {command_parts[0]}',
                'return_code': 127,
                'success': False,
                'message': f'Command not found: {command_parts[0]}'
            }
            
        except PermissionError:
            return {
                'command': command,
                'stdout': '',
                'stderr': f'Permission denied: {command}',
                'return_code': 126,
                'success': False,
                'message': f'Permission denied for command: {command}'
            }
            
        except Exception as e:
            self._logger.error(f"Error executing shell command '{command}': {e}")
            return {
                'command': command,
                'stdout': '',
                'stderr': f'Execution error: {str(e)}',
                'return_code': -1,
                'success': False,
                'message': f'Error executing command: {str(e)}'
            }
    
    async def send_message_with_features(self, message: str, session_id: Optional[str] = None,
                                       system_instruction: Optional[str] = None,
                                       process_file_refs: bool = True,
                                       allow_shell_commands: bool = False,
                                       stream: bool = False) -> Union[GeminiResponse, AsyncGenerator[str, None]]:
        """Send a message with advanced features like file references and shell commands.
        
        Args:
            message: Message content
            session_id: Optional session ID
            system_instruction: Optional system instruction
            process_file_refs: Whether to process @ file references
            allow_shell_commands: Whether to allow ! shell commands
            stream: If True, returns an async generator for streaming output.
            
        Returns:
            GeminiResponse or AsyncGenerator: Response from Gemini or a stream.
        """
        # Check for system commands
        if message.strip().startswith('/'):
            command_parts = message.strip()[1:].split()
            command = command_parts[0]
            args = command_parts[1:] if len(command_parts) > 1 else []
            
            result = await self.execute_system_command(command, args)
            
            # Return as a special response
            return GeminiResponse(
                content=f"System command result: {result}",
                session_id=session_id,
                process_id=None,
                metadata={'system_command': True, 'command_result': result}
            )
        
        # Check for shell commands
        if allow_shell_commands and message.strip().startswith('!'):
            shell_command = message.strip()[1:]
            result = await self.execute_shell_command(shell_command)
            
            return GeminiResponse(
                content=f"Shell command result: {result}",
                session_id=session_id,
                process_id=None,
                metadata={'shell_command': True, 'command_result': result}
            )
        
        # Process file references
        if process_file_refs:
            message = self.process_file_references(message)
        
        # Send normal message
        return await self.send_message(message, session_id, system_instruction, stream=stream)
