"""Process management for Gemini CLI SDK."""

import asyncio
import uuid
import time
import shutil
import logging
from dataclasses import dataclass
from typing import Dict, Optional, List
from .models import ProcessStatus, GeminiConfig, Message, ProcessInfo
from .exceptions import GeminiProcessError, GeminiNotFoundError, GeminiTimeoutError


@dataclass
class GeminiProcess:
    """Represents a Gemini CLI process."""
    process_id: str
    process: asyncio.subprocess.Process
    status: ProcessStatus
    created_at: float
    last_used: float
    session_id: Optional[str] = None
    message_count: int = 0


class ProcessManager:
    """Manages Gemini CLI processes for the SDK."""
    
    def __init__(self, config: GeminiConfig):
        """Initialize process manager.
        
        Args:
            config: Gemini configuration
        """
        self.config = config
        self.processes: Dict[str, GeminiProcess] = {}
        self.session_processes: Dict[str, str] = {}  # session_id -> process_id
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger(__name__)
        
        # Verify Gemini CLI is available
        self._verify_gemini_cli()
    
    def _verify_gemini_cli(self):
        """Verify that Gemini CLI is installed and accessible."""
        if not shutil.which(self.config.gemini_command):
            raise GeminiNotFoundError(
                f"Gemini CLI '{self.config.gemini_command}' not found in PATH. "
                "Please install Gemini CLI first."
            )
        self._logger.info(f"Verified Gemini CLI at: {self.config.gemini_command}")
    
    async def start(self):
        """Start the process manager."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._logger.info("Process manager started")
    
    async def stop(self):
        """Stop the process manager and clean up all processes."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Terminate all processes
        process_ids = list(self.processes.keys())
        for process_id in process_ids:
            await self._terminate_process(process_id)
        
        self._logger.info("Process manager stopped")
    
    async def get_or_create_process(self, session_id: Optional[str] = None) -> GeminiProcess:
        """Get an existing process or create a new one.
        
        Args:
            session_id: Optional session ID to associate with the process
            
        Returns:
            GeminiProcess: Available Gemini process
            
        Raises:
            GeminiProcessError: If process creation fails
        """
        async with self._lock:
            # Try to reuse session-bound process
            if session_id and session_id in self.session_processes:
                process_id = self.session_processes[session_id]
                if process_id in self.processes:
                    proc = self.processes[process_id]
                    if proc.status == ProcessStatus.IDLE:
                        proc.status = ProcessStatus.BUSY
                        proc.last_used = time.time()
                        self._logger.debug(f"Reusing process {process_id} for session {session_id}")
                        return proc
            
            # Find any idle process
            for proc in self.processes.values():
                if proc.status == ProcessStatus.IDLE:
                    proc.status = ProcessStatus.BUSY
                    proc.session_id = session_id
                    proc.last_used = time.time()
                    if session_id:
                        self.session_processes[session_id] = proc.process_id
                    self._logger.debug(f"Assigned idle process {proc.process_id} to session {session_id}")
                    return proc
            
            # Create new process if under limit
            if len(self.processes) < self.config.max_processes:
                return await self._create_process(session_id)
            
            # Wait for an idle process
            return await self._wait_for_idle_process(session_id)
    
    async def _create_process(self, session_id: Optional[str] = None) -> GeminiProcess:
        """Create a new Gemini process.
        
        Args:
            session_id: Optional session ID to associate
            
        Returns:
            GeminiProcess: New Gemini process
            
        Raises:
            GeminiProcessError: If process creation fails
        """
        process_id = str(uuid.uuid4())
        
        try:
            cmd = [self.config.gemini_command] + self.config.gemini_args
            self._logger.debug(f"Creating process with command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            current_time = time.time()
            gemini_proc = GeminiProcess(
                process_id=process_id,
                process=process,
                status=ProcessStatus.BUSY,
                created_at=current_time,
                last_used=current_time,
                session_id=session_id
            )
            
            self.processes[process_id] = gemini_proc
            if session_id:
                self.session_processes[session_id] = process_id
            
            self._logger.info(f"Created new Gemini process: {process_id}")
            return gemini_proc
            
        except Exception as e:
            self._logger.error(f"Failed to create Gemini process: {e}")
            raise GeminiProcessError(f"Failed to create Gemini process: {e}")
    
    async def _wait_for_idle_process(self, session_id: Optional[str] = None) -> GeminiProcess:
        """Wait for a process to become idle.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            GeminiProcess: Available process
            
        Raises:
            GeminiTimeoutError: If no process becomes available
        """
        wait_time = 0
        max_wait = 30  # Maximum wait time in seconds
        
        while wait_time < max_wait:
            await asyncio.sleep(0.1)
            wait_time += 0.1
            
            async with self._lock:
                for proc in self.processes.values():
                    if proc.status == ProcessStatus.IDLE:
                        proc.status = ProcessStatus.BUSY
                        proc.session_id = session_id
                        proc.last_used = time.time()
                        if session_id:
                            self.session_processes[session_id] = proc.process_id
                        self._logger.debug(f"Got idle process {proc.process_id} after {wait_time:.1f}s")
                        return proc
        
        raise GeminiTimeoutError("No Gemini process became available within timeout")
    
    async def send_message(self, process: GeminiProcess, message: str, 
                          context: Optional[List[Message]] = None) -> str:
        """Send a message to a Gemini process.
        
        Args:
            process: Gemini process to send message to
            message: Message content
            context: Optional conversation context
            
        Returns:
            str: Response from Gemini
            
        Raises:
            GeminiProcessError: If communication fails
            GeminiTimeoutError: If response times out
        """
        try:
            # Build message with context
            full_message = self._build_message_with_context(message, context)
            
            # Send message
            self._logger.debug(f"Sending message to process {process.process_id}")
            process.process.stdin.write(full_message.encode() + b'\n')
            await process.process.stdin.drain()
            
            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    process.process.stdout.readline(),
                    timeout=self.config.response_timeout
                )
            except asyncio.TimeoutError:
                process.status = ProcessStatus.ERROR
                raise GeminiTimeoutError(
                    f"Gemini process {process.process_id} response timeout "
                    f"after {self.config.response_timeout}s"
                )
            
            if not response_line:
                process.status = ProcessStatus.ERROR
                raise GeminiProcessError(f"Gemini process {process.process_id} closed unexpectedly")
            
            response = response_line.decode().strip()
            process.message_count += 1
            
            self._logger.debug(f"Received response from process {process.process_id}")
            return response
            
        except (GeminiTimeoutError, GeminiProcessError):
            raise
        except Exception as e:
            process.status = ProcessStatus.ERROR
            self._logger.error(f"Error communicating with Gemini process {process.process_id}: {e}")
            raise GeminiProcessError(f"Error communicating with Gemini: {e}")
        finally:
            if process.status != ProcessStatus.ERROR:
                process.status = ProcessStatus.IDLE
            process.last_used = time.time()
    
    def _build_message_with_context(self, message: str, 
                                   context: Optional[List[Message]] = None) -> str:
        """Build a message with conversation context.
        
        Args:
            message: Current message
            context: Previous conversation messages
            
        Returns:
            str: Message with context
        """
        if not context:
            return message
        
        # Build context from recent messages
        context_lines = []
        for msg in context[-10:]:  # Use last 10 messages for context
            role = msg.role.value
            content = msg.content
            context_lines.append(f"{role}: {content}")
        
        if context_lines:
            context_str = "\n".join(context_lines)
            return f"Previous conversation:\n{context_str}\n\nCurrent message: {message}"
        
        return message
    
    async def _cleanup_loop(self):
        """Background task to clean up idle processes."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_idle_processes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_idle_processes(self):
        """Clean up processes that have been idle too long."""
        current_time = time.time()
        to_remove = []
        
        async with self._lock:
            for process_id, proc in self.processes.items():
                if (proc.status == ProcessStatus.IDLE and 
                    current_time - proc.last_used > self.config.idle_timeout):
                    to_remove.append(process_id)
                elif proc.status == ProcessStatus.ERROR:
                    to_remove.append(process_id)
        
        for process_id in to_remove:
            await self._terminate_process(process_id)
        
        if to_remove:
            self._logger.info(f"Cleaned up {len(to_remove)} idle/error processes")
    
    async def _terminate_process(self, process_id: str):
        """Terminate a specific process.
        
        Args:
            process_id: ID of process to terminate
        """
        if process_id not in self.processes:
            return
        
        proc = self.processes[process_id]
        
        try:
            # Try graceful termination first
            proc.process.terminate()
            try:
                await asyncio.wait_for(proc.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill if graceful termination fails
                proc.process.kill()
                await proc.process.wait()
            
            self._logger.debug(f"Terminated process: {process_id}")
            
        except Exception as e:
            self._logger.warning(f"Error terminating process {process_id}: {e}")
        finally:
            # Clean up references
            del self.processes[process_id]
            
            # Remove session mapping
            if proc.session_id and proc.session_id in self.session_processes:
                del self.session_processes[proc.session_id]
    
    async def close_session_process(self, session_id: str):
        """Close the process associated with a session.
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_processes:
            process_id = self.session_processes[session_id]
            await self._terminate_process(process_id)
            self._logger.info(f"Closed process for session: {session_id}")
    
    def get_process_info(self, process_id: str) -> Optional[ProcessInfo]:
        """Get information about a process.
        
        Args:
            process_id: Process ID
            
        Returns:
            ProcessInfo: Process information or None if not found
        """
        if process_id not in self.processes:
            return None
        
        proc = self.processes[process_id]
        return ProcessInfo(
            process_id=process_id,
            status=proc.status,
            created_at=proc.created_at,
            last_used=proc.last_used,
            message_count=proc.message_count,
            session_id=proc.session_id
        )
    
    def list_processes(self) -> List[ProcessInfo]:
        """List all active processes.
        
        Returns:
            List[ProcessInfo]: List of process information
        """
        return [
            ProcessInfo(
                process_id=proc.process_id,
                status=proc.status,
                created_at=proc.created_at,
                last_used=proc.last_used,
                message_count=proc.message_count,
                session_id=proc.session_id
            )
            for proc in self.processes.values()
        ]
    
    def get_process_count(self) -> int:
        """Get the number of active processes.
        
        Returns:
            int: Number of active processes
        """
        return len(self.processes)
    
    def get_idle_process_count(self) -> int:
        """Get the number of idle processes.
        
        Returns:
            int: Number of idle processes
        """
        return sum(1 for proc in self.processes.values() 
                  if proc.status == ProcessStatus.IDLE)
