"""Tests for system commands functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from gemini_cli_sdk.system_commands import SystemCommands
from gemini_cli_sdk.config import ConfigManager
from gemini_cli_sdk.process_manager import ProcessManager
from gemini_cli_sdk.exceptions import GeminiValidationError, GeminiSDKError


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.max_processes = 5
    config.idle_timeout = 300
    return config


@pytest.fixture
def mock_process_manager():
    """Create a mock process manager."""
    return Mock(spec=ProcessManager)


@pytest.fixture
def system_commands(mock_process_manager, mock_config):
    """Create a SystemCommands instance with mocks."""
    return SystemCommands(mock_process_manager, mock_config)


class TestSystemCommands:
    """Test cases for SystemCommands class."""
    
    def test_init(self, mock_process_manager, mock_config):
        """Test SystemCommands initialization."""
        sys_cmd = SystemCommands(mock_process_manager, mock_config)
        assert sys_cmd.process_manager == mock_process_manager
        assert sys_cmd.config == mock_config
    
    @pytest.mark.asyncio
    async def test_execute_command_empty_command(self, system_commands):
        """Test executing empty command raises validation error."""
        with pytest.raises(GeminiValidationError, match="Command cannot be empty"):
            await system_commands.execute_command("")
    
    @pytest.mark.asyncio
    async def test_execute_command_unknown_command(self, system_commands):
        """Test executing unknown command raises validation error."""
        with pytest.raises(GeminiValidationError, match="Unknown command: /unknown"):
            await system_commands.execute_command("unknown")
    
    @pytest.mark.asyncio
    async def test_execute_command_strips_slash(self, system_commands):
        """Test that leading slash is stripped from command."""
        result = await system_commands.execute_command("/help")
        assert result['command'] == 'help'
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_help_command(self, system_commands):
        """Test help command execution."""
        result = await system_commands.execute_command("help")
        
        assert result['command'] == 'help'
        assert result['success'] is True
        assert 'available_commands' in result
        assert isinstance(result['available_commands'], list)
        assert len(result['available_commands']) > 0
    
    @pytest.mark.asyncio
    async def test_about_command_success(self, system_commands):
        """Test about command with successful subprocess."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "gemini v1.0.0"
            mock_run.return_value.stderr = ""
            
            result = await system_commands.execute_command("about")
            
            assert result['command'] == 'about'
            assert result['success'] is True
            assert result['version'] == "gemini v1.0.0"
    
    @pytest.mark.asyncio
    async def test_about_command_failure(self, system_commands):
        """Test about command with subprocess failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Command failed")
            
            result = await system_commands.execute_command("about")
            
            assert result['command'] == 'about'
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_clear_command(self, system_commands):
        """Test clear command execution."""
        result = await system_commands.execute_command("clear")
        
        assert result['command'] == 'clear'
        assert result['success'] is True
        assert 'message' in result
    
    @pytest.mark.asyncio
    async def test_stats_command_general(self, system_commands):
        """Test stats command with general type."""
        result = await system_commands.execute_command("stats")
        
        assert result['command'] == 'stats'
        assert result['type'] == 'general'
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_stats_command_model(self, system_commands):
        """Test stats command with model type."""
        result = await system_commands.execute_command("stats", ["model"])
        
        assert result['command'] == 'stats model'
        assert result['type'] == 'model'
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_chat_command_no_args(self, system_commands):
        """Test chat command without arguments."""
        result = await system_commands.execute_command("chat")
        
        assert result['command'] == 'chat'
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_chat_save_command(self, system_commands):
        """Test chat save command."""
        result = await system_commands.execute_command("chat", ["save", "test_tag"])
        
        assert result['command'] == 'chat save'
        assert result['tag'] == 'test_tag'
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_chat_list_command(self, system_commands):
        """Test chat list command."""
        result = await system_commands.execute_command("chat", ["list"])
        
        assert result['command'] == 'chat list'
        assert result['success'] is True
        assert 'checkpoints' in result
    
    @pytest.mark.asyncio
    async def test_extensions_command_no_args(self, system_commands):
        """Test extensions command without arguments."""
        result = await system_commands.execute_command("extensions")
        
        assert result['command'] == 'extensions'
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_extensions_list_command(self, system_commands):
        """Test extensions list command."""
        result = await system_commands.execute_command("extensions", ["list"])
        
        assert result['command'] == 'extensions list'
        assert result['success'] is True
        assert 'extensions' in result
    
    @pytest.mark.asyncio
    async def test_mcp_command_no_args(self, system_commands):
        """Test MCP command without arguments."""
        result = await system_commands.execute_command("mcp")
        
        assert result['command'] == 'mcp'
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_mcp_list_command(self, system_commands):
        """Test MCP list command."""
        result = await system_commands.execute_command("mcp", ["list"])
        
        assert result['command'] == 'mcp list'
        assert result['success'] is True
        assert 'servers' in result
    
    @pytest.mark.asyncio
    async def test_directory_command_no_args(self, system_commands):
        """Test directory command without arguments."""
        result = await system_commands.execute_command("directory")
        
        assert result['command'] == 'directory'
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_directory_show_command(self, system_commands):
        """Test directory show command."""
        result = await system_commands.execute_command("directory", ["show"])
        
        assert result['command'] == 'directory show'
        assert result['success'] is True
        assert 'directories' in result
    
    @pytest.mark.asyncio
    async def test_directory_add_command(self, system_commands):
        """Test directory add command."""
        result = await system_commands.execute_command("directory", ["add", "/path/to/dir"])
        
        assert result['command'] == 'directory add'
        assert result['success'] is True
        assert result['paths'] == ["/path/to/dir"]
    
    @pytest.mark.asyncio
    async def test_memory_command_no_args(self, system_commands):
        """Test memory command without arguments."""
        result = await system_commands.execute_command("memory")
        
        assert result['command'] == 'memory'
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_memory_show_command(self, system_commands):
        """Test memory show command."""
        result = await system_commands.execute_command("memory", ["show"])
        
        assert result['command'] == 'memory show'
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_memory_add_command(self, system_commands):
        """Test memory add command."""
        result = await system_commands.execute_command("memory", ["add", "test content"])
        
        assert result['command'] == 'memory add'
        assert result['content'] == 'test content'
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_tools_command(self, system_commands):
        """Test tools command."""
        result = await system_commands.execute_command("tools")
        
        assert result['command'] == 'tools'
        assert result['success'] is True
        assert 'tools' in result
        assert 'show_descriptions' in result
    
    @pytest.mark.asyncio
    async def test_tools_command_with_desc(self, system_commands):
        """Test tools command with descriptions."""
        result = await system_commands.execute_command("tools", ["desc"])
        
        assert result['command'] == 'tools'
        assert result['success'] is True
        assert result['show_descriptions'] is True
    
    @pytest.mark.asyncio
    async def test_quit_command(self, system_commands):
        """Test quit command."""
        result = await system_commands.execute_command("quit")
        
        assert result['command'] == 'quit'
        assert result['success'] is True
        assert result['exit'] is True
    
    @pytest.mark.asyncio
    async def test_docs_command(self, system_commands):
        """Test docs command."""
        with patch('webbrowser.open') as mock_open:
            result = await system_commands.execute_command("docs")
            
            assert result['command'] == 'docs'
            assert result['success'] is True
            mock_open.assert_called_once_with('https://docs.gemini.google.com/cli')
    
    @pytest.mark.asyncio
    async def test_docs_command_failure(self, system_commands):
        """Test docs command with webbrowser failure."""
        with patch('webbrowser.open') as mock_open:
            mock_open.side_effect = Exception("Browser error")
            
            result = await system_commands.execute_command("docs")
            
            assert result['command'] == 'docs'
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_privacy_command(self, system_commands):
        """Test privacy command."""
        result = await system_commands.execute_command("privacy")
        
        assert result['command'] == 'privacy'
        assert result['success'] is True
        assert 'message' in result
    
    @pytest.mark.asyncio
    async def test_command_execution_exception(self, system_commands):
        """Test command execution with unexpected exception."""
        # Mock a command method to raise an exception
        with patch.object(system_commands, '_help', side_effect=Exception("Unexpected error")):
            with pytest.raises(GeminiSDKError, match="Command execution failed"):
                await system_commands.execute_command("help")


@pytest.mark.asyncio
async def test_system_commands_integration():
    """Integration test for system commands."""
    config = Mock()
    config.max_processes = 5
    process_manager = Mock()
    
    sys_cmd = SystemCommands(process_manager, config)
    
    # Test multiple commands in sequence
    commands = ["help", "clear", "stats", "tools"]
    
    for command in commands:
        result = await sys_cmd.execute_command(command)
        assert result['success'] is True
        assert result['command'] == command


if __name__ == "__main__":
    pytest.main([__file__])
