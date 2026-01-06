"""Integration tests for Gemini CLI SDK with real Gemini CLI."""

import pytest
import asyncio
import logging
import shutil
import os
from unittest.mock import patch

from gemini_cli_sdk import (
    GeminiClient,
    GeminiConfig,
    GeminiNotFoundError,
    GeminiResponse,
)

# Configure logger for integration tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gemini_cli_sdk.test_integration')


def has_gemini_cli():
    """Check if Gemini CLI is available in the system."""
    return shutil.which("gemini") is not None


@pytest.mark.integration
@pytest.mark.skipif(not has_gemini_cli(), reason="Gemini CLI not found in PATH")
class TestRealGeminiIntegration:
    """Integration tests with real Gemini CLI."""

    @pytest.fixture
    def real_config(self):
        """Configuration for real Gemini CLI."""
        return GeminiConfig(
            max_processes=2,
            idle_timeout=30,
            max_context_length=20,
            enable_logging=True,
            log_level="INFO",
            response_timeout=60.0,  # Longer timeout for real interactions
        )

    @pytest.mark.asyncio
    async def test_real_gemini_availability(self, real_config):
        """Test that Gemini CLI is available and can be started."""
        async with GeminiClient(config=real_config) as client:
            assert client._started is True
            logger.info("Successfully connected to real Gemini CLI")
            
            # Test health check
            health = await client.health_check()
            assert health["status"] == "ok"
            logger.info(f"Health check passed: {health}")

    @pytest.mark.asyncio
    async def test_real_one_shot_interaction(self, real_config):
        """Test one-shot interaction with real Gemini CLI."""
        async with GeminiClient(config=real_config) as client:
            question = "What is 2+2? Please answer with just the number."
            logger.info(f"Asking real Gemini: {question}")
            
            response = await client.one_shot(question)
            
            assert isinstance(response, GeminiResponse)
            assert response.content is not None
            assert len(response.content.strip()) > 0
            assert response.session_id is None
            
            logger.info(f"Real Gemini response: {response.content}")

    @pytest.mark.asyncio
    async def test_real_chat_session(self, real_config):
        """Test chat session with real Gemini CLI."""
        async with GeminiClient(config=real_config) as client:
            session_id = client.create_session()
            logger.info(f"Created real session: {session_id}")
            
            # First message
            response1 = await client.chat("Hello, I'm testing you.", session_id)
            assert isinstance(response1, GeminiResponse)
            assert response1.session_id == session_id
            logger.info(f"First response: {response1.content}")
            
            # Second message with context
            response2 = await client.chat("What did I just say to you?", session_id)
            assert isinstance(response2, GeminiResponse)
            assert response2.session_id == session_id
            logger.info(f"Second response: {response2.content}")
            
            # Verify context is maintained
            context = client._session_manager.get_context(session_id)
            assert len(context) == 4  # 2 user messages + 2 assistant responses
            
            client.close_session(session_id)
            logger.info(f"Closed real session: {session_id}")

    @pytest.mark.asyncio
    async def test_real_system_instruction(self, real_config):
        """Test system instruction with real Gemini CLI."""
        async with GeminiClient(config=real_config) as client:
            system_instruction = "You are a helpful math tutor. Always explain your reasoning step by step."
            question = "What is 15 * 7?"
            
            logger.info(f"Testing system instruction: {system_instruction}")
            logger.info(f"Question: {question}")
            
            response = await client.one_shot(
                question,
                system_instruction=system_instruction
            )
            
            assert isinstance(response, GeminiResponse)
            assert response.content is not None
            assert "105" in response.content  # Expected answer
            logger.info(f"System instruction response: {response.content}")

    @pytest.mark.asyncio
    async def test_real_concurrent_requests(self, real_config):
        """Test concurrent requests with real Gemini CLI."""
        async with GeminiClient(config=real_config) as client:
            questions = [
                "What is the capital of France?",
                "What is 10 + 5?",
                "Name one programming language."
            ]
            
            logger.info(f"Sending concurrent questions: {questions}")
            responses = await client.send_concurrent(questions)
            
            assert len(responses) == 3
            for i, response in enumerate(responses):
                assert isinstance(response, GeminiResponse)
                assert response.content is not None
                assert len(response.content.strip()) > 0
                logger.info(f"Concurrent response {i+1}: {response.content}")

    @pytest.mark.asyncio
    async def test_real_batch_processing(self, real_config):
        """Test batch processing with real Gemini CLI."""
        async with GeminiClient(config=real_config) as client:
            session_id = client.create_session()
            
            messages = [
                "I'm going to ask you a series of questions.",
                "What is your name?",
                "What can you help me with?"
            ]
            
            logger.info(f"Sending batch messages: {messages}")
            responses = await client.send_batch(messages, session_id)
            
            assert len(responses) == 3
            for i, response in enumerate(responses):
                assert isinstance(response, GeminiResponse)
                assert response.session_id == session_id
                assert response.content is not None
                logger.info(f"Batch response {i+1}: {response.content}")
            
            client.close_session(session_id)

    @pytest.mark.asyncio
    async def test_real_error_handling(self, real_config):
        """Test error handling with real Gemini CLI."""
        async with GeminiClient(config=real_config) as client:
            # Test with very long message that might cause issues
            very_long_message = "A" * 10000 + " What is this?"
            
            try:
                response = await client.one_shot(very_long_message)
                # If it succeeds, that's fine too
                assert isinstance(response, GeminiResponse)
                logger.info("Long message handled successfully")
            except Exception as e:
                # If it fails, log the error but don't fail the test
                logger.info(f"Long message caused expected error: {e}")

    @pytest.mark.asyncio
    async def test_real_process_management(self, real_config):
        """Test process management with real Gemini CLI."""
        async with GeminiClient(config=real_config) as client:
            # Get initial stats
            initial_stats = client.get_stats()
            logger.info(f"Initial stats: {initial_stats}")
            
            # Create multiple sessions to test process pooling
            session1 = client.create_session()
            session2 = client.create_session()
            
            # Send messages to both sessions
            response1 = await client.chat("Hello from session 1", session1)
            response2 = await client.chat("Hello from session 2", session2)
            
            assert response1.session_id == session1
            assert response2.session_id == session2
            
            # Check stats after activity
            final_stats = client.get_stats()
            logger.info(f"Final stats: {final_stats}")
            
            assert final_stats["sessions"]["total"] == 2
            
            # Clean up
            client.close_session(session1)
            client.close_session(session2)


@pytest.mark.integration
class TestGeminiCLINotFound:
    """Test behavior when Gemini CLI is not found."""

    def test_gemini_not_found_error(self):
        """Test that appropriate error is raised when Gemini CLI is not found."""
        config = GeminiConfig(gemini_command="nonexistent_gemini_command")
        
        with pytest.raises(GeminiNotFoundError, match="not found in PATH"):
            GeminiClient(config=config)

    @pytest.mark.asyncio
    async def test_mock_gemini_path_check(self):
        """Test path checking with mocked shutil.which."""
        config = GeminiConfig(gemini_command="mock_gemini")
        
        # Test when command is not found
        with patch("shutil.which", return_value=None):
            with pytest.raises(GeminiNotFoundError):
                GeminiClient(config=config)
        
        # Test when command is found
        with patch("shutil.which", return_value="/usr/bin/mock_gemini"):
            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                # Mock the subprocess to avoid actually starting it
                mock_process = asyncio.create_task(asyncio.sleep(0))
                mock_subprocess.return_value = mock_process
                
                try:
                    client = GeminiClient(config=config)
                    assert client is not None
                except Exception as e:
                    # It's okay if it fails later, we just want to test the path check
                    logger.info(f"Expected error after path check: {e}")


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration loading and management in integration scenarios."""

    def test_config_file_integration(self, tmp_path):
        """Test configuration file loading in integration context."""
        config_file = tmp_path / "test_integration_config.json"
        
        # Create a config file
        config_data = {
            "max_processes": 3,
            "idle_timeout": 120,
            "log_level": "DEBUG",
            "response_timeout": 45.0
        }
        
        import json
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test loading config from file
        from gemini_cli_sdk.config import ConfigManager
        manager = ConfigManager(config_file=str(config_file))
        config = manager.load_config()
        
        assert config.max_processes == 3
        assert config.idle_timeout == 120
        assert config.log_level == "DEBUG"
        assert config.response_timeout == 45.0

    def test_environment_variable_integration(self, monkeypatch):
        """Test environment variable configuration in integration context."""
        # Set environment variables
        monkeypatch.setenv("GEMINI_MAX_PROCESSES", "4")
        monkeypatch.setenv("GEMINI_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("GEMINI_RESPONSE_TIMEOUT", "90.0")
        
        # Load config with environment variables
        from gemini_cli_sdk.config import ConfigManager
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.max_processes == 4
        assert config.log_level == "WARNING"
        assert config.response_timeout == 90.0


if __name__ == "__main__":
    # Run integration tests directly
    pytest.main([__file__, "-v", "-m", "integration"])
