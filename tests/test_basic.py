"""Basic tests for Gemini CLI SDK."""

import pytest
import pytest_asyncio
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
import os
import json
import tempfile

from gemini_cli_sdk import (
    GeminiClient,
    GeminiConfig,
    SessionManager,
    MessageRole,
    GeminiValidationError,
    GeminiSessionError,
    GeminiConfigError,
    GeminiResponse,
)
from gemini_cli_sdk.config import ConfigManager
from gemini_cli_sdk.models import Message


# Configure a logger for tests to see output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gemini_cli_sdk.test_basic')


@pytest.fixture
def mock_gemini_cli_process():
    """Mock a Gemini CLI process."""
    mock_process = AsyncMock()
    mock_process.stdout.readline.side_effect = [
        b'{"response": "mocked response 1"}\n',
        b'{"response": "mocked response 2"}\n',
        b'{"response": "mocked response 3"}\n',
        asyncio.CancelledError,  # Simulate process termination
    ]
    mock_process.poll.return_value = None  # Process is running
    mock_process.pid = 12345
    return mock_process


@pytest.fixture
def mock_gemini_config():
    """Returns a mock GeminiConfig instance."""
    return GeminiConfig(
        gemini_command="mock_gemini",
        gemini_args=["--mock-arg"],
        max_processes=1,
        idle_timeout=1,
        max_context_length=10,
        enable_logging=True,
        log_level="DEBUG",
    )


@pytest.fixture
def mock_config_manager(mock_gemini_config):
    """Returns a mock ConfigManager instance."""
    manager = ConfigManager(config_file="/tmp/mock_config.json")
    manager._config = mock_gemini_config  # pylint: disable=protected-access
    return manager


@pytest.fixture
def session_manager(mock_config_manager):
    """Returns a SessionManager instance."""
    return SessionManager(mock_config_manager)


@pytest_asyncio.fixture
async def client_with_mock_process(mock_gemini_config, mock_gemini_cli_process):
    """Returns a GeminiClient instance for testing with a mocked process."""
    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_gemini_cli_process
    ), patch(
        "gemini_cli_sdk.process_manager.GeminiConfig", return_value=mock_gemini_config
    ), patch(
        "shutil.which", return_value="/usr/bin/mock_gemini"
    ):
        async with GeminiClient(config=mock_gemini_config) as c:
            yield c


class TestGeminiConfig:
    """Tests for GeminiConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GeminiConfig()
        assert config.max_processes == 5
        assert config.idle_timeout == 300
        assert config.max_context_length == 50
        assert config.gemini_command == "gemini"
        assert config.gemini_args == ["--interactive", "--json-output"]
        assert config.enable_logging is True
        assert config.log_level == "INFO"
        assert config.response_timeout == 30.0
        assert config.cleanup_interval == 60

    def test_custom_config(self):
        """Test custom configuration values."""
        config = GeminiConfig(
            max_processes=10,
            idle_timeout=600,
            max_context_length=100,
            gemini_command="my_gemini",
            gemini_args=["--custom-arg"],
            enable_logging=False,
            log_level="DEBUG",
            response_timeout=60.0,
            cleanup_interval=120,
        )
        assert config.max_processes == 10
        assert config.idle_timeout == 600
        assert config.max_context_length == 100
        assert config.gemini_command == "my_gemini"
        assert config.gemini_args == ["--custom-arg"]
        assert config.enable_logging is False
        assert config.log_level == "DEBUG"
        assert config.response_timeout == 60.0
        assert config.cleanup_interval == 120


class TestConfigManager:
    """Tests for ConfigManager."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down mock config file."""
        self.test_config_file = "/tmp/test_gemini_cli_sdk.json"
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        yield
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)

    def test_load_default_config(self):
        """Test loading default configuration."""
        manager = ConfigManager(config_file=self.test_config_file)
        config = manager.load_config()
        assert config.max_processes == 5

    def test_load_custom_config_from_file(self):
        """Test loading custom configuration from file."""
        custom_config_data = {
            "max_processes": 8,
            "log_level": "WARNING",
            "gemini_args": ["--test"],
        }
        with open(self.test_config_file, "w", encoding="utf-8") as f:
            json.dump(custom_config_data, f)

        manager = ConfigManager(config_file=self.test_config_file)
        config = manager.load_config()
        assert config.max_processes == 8
        assert config.log_level == "WARNING"
        assert config.gemini_args == ["--test"]
        assert config.idle_timeout == 300  # Default value

    def test_load_config_with_env_vars(self, monkeypatch):
        """Test loading configuration with environment variables."""
        monkeypatch.setenv("GEMINI_MAX_PROCESSES", "12")
        monkeypatch.setenv("GEMINI_LOG_LEVEL", "ERROR")
        monkeypatch.setenv("GEMINI_ARGS", "--env-arg1 --env-arg2")

        manager = ConfigManager(config_file=self.test_config_file)
        config = manager.load_config()
        assert config.max_processes == 12
        assert config.log_level == "ERROR"
        assert config.gemini_args == ["--env-arg1", "--env-arg2"]

    def test_env_vars_override_file(self, monkeypatch):
        """Test environment variables override file configuration."""
        file_config_data = {"max_processes": 8, "log_level": "WARNING"}
        with open(self.test_config_file, "w", encoding="utf-8") as f:
            json.dump(file_config_data, f)

        monkeypatch.setenv("GEMINI_MAX_PROCESSES", "15")

        manager = ConfigManager(config_file=self.test_config_file)
        config = manager.load_config()
        assert config.max_processes == 15
        assert config.log_level == "WARNING"

    def test_invalid_config_file_raises_error(self):
        """Test invalid config file raises error."""
        with open(self.test_config_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        manager = ConfigManager(config_file=self.test_config_file)
        with pytest.raises(GeminiConfigError):
            manager.load_config()

    def test_save_config(self):
        """Test saving configuration to file."""
        manager = ConfigManager(config_file=self.test_config_file)
        config_to_save = GeminiConfig(max_processes=7, enable_logging=False)
        manager.save_config(config_to_save)

        loaded_manager = ConfigManager(config_file=self.test_config_file)
        loaded_config = loaded_manager.load_config()
        assert loaded_config.max_processes == 7
        assert loaded_config.enable_logging is False
        assert loaded_config.log_level == "INFO"  # Default value

    def test_get_config_dict(self, mock_config_manager):
        """Test getting configuration as a dictionary."""
        config_dict = mock_config_manager.get_config_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["max_processes"] == mock_config_manager._config.max_processes


class TestSessionManager:
    """Tests for SessionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_manager = SessionManager(max_context_length=10)

    def test_create_session(self):
        """Test creating a new session."""
        session_id = self.session_manager.create_session()
        assert session_id is not None
        assert self.session_manager.session_exists(session_id)

    def test_session_with_metadata(self):
        """Test session creation with metadata."""
        metadata = {"user": "test", "topic": "programming"}
        session_id = self.session_manager.create_session(
            user_id="test_user",
            metadata=metadata
        )

        session_info = self.session_manager.get_session_info(session_id)
        assert session_info.metadata == metadata

    def test_add_message(self):
        """Test adding messages to session."""
        session_id = self.session_manager.create_session()

        self.session_manager.add_message(
            session_id,
            MessageRole.USER,
            "Hello"
        )

        context = self.session_manager.get_context(session_id)
        assert len(context) == 1
        assert context[0].role == MessageRole.USER
        assert context[0].content == "Hello"

    def test_context_limit(self):
        """Test context length limiting."""
        session_id = self.session_manager.create_session()

        # Add more messages than the limit
        for i in range(15):
            self.session_manager.add_message(
                session_id,
                MessageRole.USER,
                f"Message {i}"
            )

        context = self.session_manager.get_context(session_id)
        assert len(context) == 10  # Should be limited to max_context_length

    def test_nonexistent_session(self):
        """Test operations on non-existent session."""
        with pytest.raises(GeminiSessionError):
            self.session_manager.get_session("nonexistent")

    def test_close_session(self):
        """Test session closure."""
        session_id = self.session_manager.create_session()
        assert self.session_manager.session_exists(session_id)

        self.session_manager.close_session(session_id)
        assert not self.session_manager.session_exists(session_id)

    def test_list_sessions(self):
        """Test listing sessions."""
        session1 = self.session_manager.create_session()
        session2 = self.session_manager.create_session()

        sessions = self.session_manager.list_sessions()
        assert len(sessions) == 2

        session_ids = [s.session_id for s in sessions]
        assert session1 in session_ids
        assert session2 in session_ids


class TestGeminiClient:
    """Tests for GeminiClient."""

    @pytest.fixture
    def mock_process_manager(self):
        """Mock process manager."""
        mock = Mock()
        mock.start = AsyncMock()
        mock.stop = AsyncMock()
        mock.get_or_create_process = AsyncMock()
        mock.send_message = AsyncMock(return_value=GeminiResponse(content="Mocked response"))
        mock.get_process_count = Mock(return_value=1)
        mock.get_idle_process_count = Mock(return_value=0)
        return mock

    @pytest.fixture
    def client_with_mock(self, mock_process_manager):
        """Create client with mocked process manager."""
        config = GeminiConfig()
        client = GeminiClient(config=config)
        client.process_manager = mock_process_manager
        return client

    @pytest.mark.asyncio
    async def test_client_context_manager(self, client_with_mock_process):
        """Test client as async context manager."""
        # This test now uses the fixture that mocks the actual process
        async with client_with_mock_process as client:
            assert client._started is True
            logger.info("Client started in context manager test.")
        assert client._started is False
        logger.info("Client stopped in context manager test.")

    @pytest.mark.asyncio
    async def test_one_shot(self, client_with_mock_process):
        """Test one_shot method."""
        question = "Hello Gemini"
        logger.info(f"Test one_shot with question: {question}")
        response = await client_with_mock_process.one_shot(question)
        logger.info(f"One_shot response: {response.content}")
        assert response.content == "mocked response 1"
        assert response.session_id is None

    @pytest.mark.asyncio
    async def test_chat_with_session(self, client_with_mock_process):
        """Test chat method with session management."""
        session_id = client_with_mock_process.create_session()
        logger.info(f"Created session: {session_id}")

        question1 = "First message"
        response1 = await client_with_mock_process.chat(question1, session_id)
        logger.info(f"Chat message 1: {question1}, Response: {response1.content}")
        assert response1.content == "mocked response 1"
        assert response1.session_id == session_id
        assert len(client_with_mock_process._session_manager.get_context(session_id)) == 2

        question2 = "Second message"
        response2 = await client_with_mock_process.chat(question2, session_id)
        logger.info(f"Chat message 2: {question2}, Response: {response2.content}")
        assert response2.content == "mocked response 2"
        assert response2.session_id == session_id
        assert len(client_with_mock_process._session_manager.get_context(session_id)) == 4
        client_with_mock_process.close_session(session_id)
        logger.info(f"Closed session: {session_id}")


    @pytest.mark.asyncio
    async def test_send_batch(self, client_with_mock_process):
        """Test send_batch method."""
        messages = ["Batch message 1", "Batch message 2"]
        session_id = client_with_mock_process.create_session()
        logger.info(f"Created session for batch: {session_id}")
        responses = await client_with_mock_process.send_batch(messages, session_id)

        assert len(responses) == 2
        assert responses[0].content == "mocked response 1"
        assert responses[1].content == "mocked response 2"
        assert len(client_with_mock_process._session_manager.get_context(session_id)) == 4
        logger.info(f"Batch messages sent, responses received. Session: {session_id}")
        client_with_mock_process.close_session(session_id)


    @pytest.mark.asyncio
    async def test_send_concurrent(self, client_with_mock_process):
        """Test send_concurrent method."""
        messages = ["Concurrent message 1", "Concurrent message 2"]
        logger.info("Sending concurrent messages.")
        responses = await client_with_mock_process.send_concurrent(messages)

        assert len(responses) == 2
        # Order might not be guaranteed for concurrent, but content should match
        assert {r.content for r in responses} == {"mocked response 1", "mocked response 2"}
        assert all(r.session_id is None for r in responses)
        logger.info("Concurrent messages sent, responses received.")


    @pytest.mark.asyncio
    async def test_system_instruction_with_logging(self, client_with_mock_process):
        """测试带系统指令的真实交互和日志输出"""
        system_instruction = "你是一个专业的Python编程助手，请用简洁明了的方式回答问题。"
        question = "如何定义一个Python函数？"
        
        logger.info(f"Test one_shot with system instruction: {system_instruction}")
        logger.info(f"Question: {question}")

        response = await client_with_mock_process.one_shot(
            question,
            system_instruction=system_instruction
        )
        
        logger.info(f"Response: {response.content}")
        assert response.content == "mocked response 1"
        assert response.session_id is None


    @pytest.mark.asyncio
    async def test_file_reference_with_logging(self, client_with_mock_process):
        """测试文件引用处理的日志输出"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("Hello, this is a test file for logging!")
            temp_filename = temp_file.name
        
        message = f"Please analyze this file: @{temp_filename}"
        logger.info(f"Test file reference with message: {message}")
        
        response = await client_with_mock_process.send_message_with_features(
            message,
            process_file_refs=True
        )
        
        logger.info(f"File reference response: {response.content}")
        assert "Hello, this is a test file for logging!" in response.content
        os.unlink(temp_filename)


    @pytest.mark.asyncio
    async def test_shell_commands_with_logging(self, client_with_mock_process):
        """测试Shell命令执行的日志输出"""
        command = "!echo Hello from test"
        logger.info(f"Test shell command with message: {command}")
        
        response = await client_with_mock_process.send_message_with_features(
            command,
            allow_shell_commands=True
        )
        
        logger.info(f"Shell command response: {response.content}")
        assert "Hello from test" in response.content


    def test_validation_errors(self, client_with_mock):
        """Test validation errors."""
        with pytest.raises(GeminiValidationError, match="Message cannot be empty"):
            asyncio.run(client_with_mock.send_message(""))  # Empty message
        with pytest.raises(GeminiValidationError, match="Message cannot be empty"):
            asyncio.run(client_with_mock.chat("", client_with_mock.create_session()))

    @pytest.mark.asyncio
    async def test_session_management(self, client_with_mock_process):
        """Test create_session and close_session methods."""
        session_id = client_with_mock_process.create_session()
        logger.info(f"Session management test: Created session {session_id}")
        assert session_id in client_with_mock_process._session_manager._sessions
        client_with_mock_process.close_session(session_id)
        logger.info(f"Session management test: Closed session {session_id}")
        assert session_id not in client_with_mock_process._session_manager._sessions

    @pytest.mark.asyncio
    async def test_get_stats(self, client_with_mock_process):
        """Test get_stats method."""
        stats = client_with_mock_process.get_stats()
        logger.info(f"Client stats: {stats}")
        assert "sessions" in stats
        assert "processes" in stats
        assert stats["sessions"]["total"] == 0
        assert stats["processes"]["total"] == 0

        client_with_mock_process.create_session()
        stats = client_with_mock_process.get_stats()
        logger.info(f"Client stats after creating session: {stats}")
        assert stats["sessions"]["total"] == 1
        assert stats["processes"]["total"] == 1  # A process is allocated for the session
        client_with_mock_process.close_session(list(client_with_mock_process._session_manager._sessions.keys())[0])


    @pytest.mark.asyncio
    async def test_config_operations(self, client_with_mock_process, mock_config_manager, mock_gemini_config):
        """Test config operations."""
        # Test get_config
        retrieved_config = client_with_mock_process.get_config()
        logger.info(f"Retrieved config: {retrieved_config}")
        assert retrieved_config.max_processes == mock_gemini_config.max_processes

        # Test set_config
        new_config = GeminiConfig(max_processes=2, idle_timeout=2)
        client_with_mock_process.set_config(new_config)
        logger.info(f"New config set: {client_with_mock_process._config}")
        assert client_with_mock_process._config.max_processes == 2
        assert client_with_mock_process._process_manager._config.max_processes == 2


@pytest.mark.asyncio
async def test_health_check(client_with_mock_process):
    """Test health_check method."""
    health = await client_with_mock_process.health_check()
    logger.info(f"Health check result: {health}")
    assert health["status"] == "ok"
    assert "process_manager" in health
    assert "session_manager" in health


def test_import_all():
    """Test that all public APIs can be imported."""
    from gemini_cli_sdk import (
        GeminiClient,
        GeminiConfig,
        GeminiResponse,
        SessionInfo,
        Message,
        MessageRole,
        ProcessStatus,
        ProcessInfo,
        GeminiSDKError,
        GeminiProcessError,
        GeminiSessionError,
        GeminiConfigError,
        GeminiTimeoutError,
        GeminiNotFoundError,
        GeminiConnectionError,
        GeminiValidationError,
        ConfigManager,
        # validate_session_id,  # These are internal utilities, not public API
        # format_timestamp,
        # sanitize_message,
        # format_duration,
        # get_env_config
    )

    # Basic smoke test
    assert GeminiClient is not None
    assert GeminiConfig is not None
    assert MessageRole.USER is not None
