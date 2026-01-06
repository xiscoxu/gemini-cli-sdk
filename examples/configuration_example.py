"""Configuration examples for Gemini CLI SDK."""

import asyncio
import os
from gemini_cli_sdk import GeminiClient, GeminiConfig, ConfigManager


async def default_config_example():
    """Example using default configuration."""
    print("=== Default Configuration Example ===")
    
    async with GeminiClient() as client:
        config = client.get_config()
        print("Default configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        response = await client.one_shot("Hello!")
        print(f"Response: {response}")


async def custom_config_example():
    """Example using custom configuration."""
    print("\n=== Custom Configuration Example ===")
    
    # Create custom configuration
    config = GeminiConfig(
        max_processes=3,
        idle_timeout=600,  # 10 minutes
        max_context_length=100,
        response_timeout=60.0,
        enable_logging=True,
        log_level="DEBUG"
    )
    
    async with GeminiClient(config=config) as client:
        print("Custom configuration:")
        config_dict = client.get_config()
        for key, value in config_dict.items():
            print(f"  {key}: {value}")
        
        response = await client.one_shot("What's the weather like?")
        print(f"Response: {response}")


async def config_file_example():
    """Example using configuration file."""
    print("\n=== Configuration File Example ===")
    
    # Create a temporary config file
    config_file = "/tmp/gemini_test_config.json"
    config_content = {
        "max_processes": 2,
        "idle_timeout": 120,
        "max_context_length": 20,
        "gemini_command": "gemini",
        "gemini_args": ["--interactive"],
        "enable_logging": True,
        "log_level": "INFO",
        "response_timeout": 45.0,
        "cleanup_interval": 30
    }
    
    import json
    with open(config_file, 'w') as f:
        json.dump(config_content, f, indent=2)
    
    try:
        # Use config file
        async with GeminiClient(config_file=config_file) as client:
            print(f"Configuration loaded from {config_file}:")
            config_dict = client.get_config()
            for key, value in config_dict.items():
                print(f"  {key}: {value}")
            
            response = await client.one_shot("Hello from config file!")
            print(f"Response: {response}")
    
    finally:
        # Clean up
        if os.path.exists(config_file):
            os.remove(config_file)


async def environment_config_example():
    """Example using environment variables."""
    print("\n=== Environment Configuration Example ===")
    
    # Set environment variables
    env_vars = {
        'GEMINI_MAX_PROCESSES': '4',
        'GEMINI_IDLE_TIMEOUT': '180',
        'GEMINI_MAX_CONTEXT_LENGTH': '30',
        'GEMINI_ENABLE_LOGGING': 'true',
        'GEMINI_LOG_LEVEL': 'WARNING',
        'GEMINI_RESPONSE_TIMEOUT': '25.0'
    }
    
    # Backup original environment
    original_env = {}
    for key in env_vars:
        original_env[key] = os.environ.get(key)
    
    try:
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
        
        async with GeminiClient() as client:
            print("Configuration from environment variables:")
            config_dict = client.get_config()
            for key, value in config_dict.items():
                print(f"  {key}: {value}")
            
            response = await client.one_shot("Hello from environment!")
            print(f"Response: {response}")
    
    finally:
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


async def config_manager_example():
    """Example using ConfigManager directly."""
    print("\n=== ConfigManager Example ===")
    
    config_manager = ConfigManager()
    
    # Load default config
    config = config_manager.load_config()
    print("Loaded configuration:")
    print(f"  Max processes: {config.max_processes}")
    print(f"  Idle timeout: {config.idle_timeout}")
    print(f"  Context length: {config.max_context_length}")
    
    # Modify and save config
    config.max_processes = 6
    config.response_timeout = 40.0
    
    # Note: In a real scenario, you might want to save to a different file
    # config_manager.save_config(config)
    print("Modified configuration (not saved):")
    print(f"  Max processes: {config.max_processes}")
    print(f"  Response timeout: {config.response_timeout}")


async def runtime_config_update():
    """Example of updating configuration at runtime."""
    print("\n=== Runtime Configuration Update Example ===")
    
    async with GeminiClient() as client:
        print("Initial configuration:")
        initial_config = client.get_config()
        print(f"  Max processes: {initial_config['max_processes']}")
        print(f"  Response timeout: {initial_config['response_timeout']}")
        
        # Update configuration
        client.update_config(
            max_processes=7,
            response_timeout=50.0,
            idle_timeout=400
        )
        
        print("\nUpdated configuration:")
        updated_config = client.get_config()
        print(f"  Max processes: {updated_config['max_processes']}")
        print(f"  Response timeout: {updated_config['response_timeout']}")
        print(f"  Idle timeout: {updated_config['idle_timeout']}")
        
        response = await client.one_shot("Hello with updated config!")
        print(f"Response: {response}")


async def main():
    """Run all configuration examples."""
    try:
        await default_config_example()
        await custom_config_example()
        await config_file_example()
        await environment_config_example()
        await config_manager_example()
        await runtime_config_update()
        
    except Exception as e:
        print(f"Error running configuration examples: {e}")
        print("Make sure Gemini CLI is installed and available in PATH")


if __name__ == "__main__":
    asyncio.run(main())
