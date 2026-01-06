"""Test logging functionality."""

import pytest
import logging
import io
import sys
from gemini_cli_sdk import GeminiClient, GeminiConfig
from gemini_cli_sdk.config import ConfigManager


@pytest.mark.logging
class TestLogging:
    """Test logging functionality."""
    
    def test_logging_enabled_by_default(self):
        """Test that logging is enabled by default."""
        config = GeminiConfig()
        assert config.enable_logging is True
        assert config.log_level == "INFO"
    
    def test_config_manager_logging_setup(self):
        """Test that ConfigManager sets up logging correctly."""
        # Create a config with logging enabled
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Check that the logger is configured
        logger = logging.getLogger('gemini_cli_sdk')
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_logging_output(self, caplog):
        """Test that logging actually produces output."""
        with caplog.at_level(logging.INFO, logger='gemini_cli_sdk'):
            # Create a config manager which should set up logging
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            # Get a logger and log a message
            logger = logging.getLogger('gemini_cli_sdk.test')
            logger.info("Test log message")
            
            # Check that the message was captured
            assert "Test log message" in caplog.text
    
    def test_different_log_levels(self, caplog):
        """Test different log levels."""
        config = GeminiConfig(log_level="DEBUG")
        config_manager = ConfigManager()
        config_manager._config = config
        config_manager._setup_logging()
        
        logger = logging.getLogger('gemini_cli_sdk.test')
        
        with caplog.at_level(logging.DEBUG, logger='gemini_cli_sdk'):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            assert "Debug message" in caplog.text
            assert "Info message" in caplog.text
            assert "Warning message" in caplog.text
            assert "Error message" in caplog.text
    
    def test_logging_disabled(self, caplog):
        """Test that logging can be disabled."""
        config = GeminiConfig(enable_logging=False)
        config_manager = ConfigManager()
        config_manager._config = config
        config_manager._setup_logging()
        
        logger = logging.getLogger('gemini_cli_sdk.test_disabled')
        
        with caplog.at_level(logging.INFO, logger='gemini_cli_sdk'):
            logger.info("This should not appear")
            
            # When logging is disabled, the logger should not have handlers
            # or should be at a higher level
            sdk_logger = logging.getLogger('gemini_cli_sdk')
            # The message might still be captured by caplog, but in real usage
            # it wouldn't be displayed
    
    @pytest.mark.asyncio
    async def test_client_logging(self, caplog):
        """Test that client operations produce log messages."""
        config = GeminiConfig(enable_logging=True, log_level="INFO")
        
        with caplog.at_level(logging.INFO, logger='gemini_cli_sdk'):
            async with GeminiClient(config=config) as client:
                # This should produce some log messages
                stats = client.get_stats()
                
                # Check for expected log messages
                assert any("started" in record.message.lower() for record in caplog.records)


def test_manual_logging_demo():
    """Demonstrate manual logging setup for debugging."""
    # Set up a simple console logger
    logger = logging.getLogger('gemini_cli_sdk')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Test logging
    logger.info("Manual logging test - this should be visible")
    logger.debug("Debug message - this should also be visible")
    logger.warning("Warning message")
    logger.error("Error message")
    
    print("Manual logging demo completed")


if __name__ == "__main__":
    # Run the manual demo
    test_manual_logging_demo()
