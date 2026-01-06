"""Example demonstrating Gemini CLI system commands usage."""

import asyncio
import logging
from gemini_cli_sdk import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate system commands functionality."""
    
    async with GeminiClient() as client:
        print("=== Gemini CLI SDK - System Commands Demo ===\n")
        
        # 1. Get version information
        print("1. Getting version information...")
        about_result = await client.system_about()
        print(f"About: {about_result}\n")
        
        # 2. Get help information
        print("2. Getting help information...")
        help_result = await client.system_help()
        print(f"Available commands: {len(help_result.get('available_commands', []))}")
        for cmd in help_result.get('available_commands', [])[:5]:  # Show first 5
            print(f"  - {cmd}")
        print("  ...\n")
        
        # 3. Get system statistics
        print("3. Getting system statistics...")
        stats_result = await client.system_stats()
        print(f"Stats: {stats_result}\n")
        
        # 4. Demonstrate chat checkpoint management
        print("4. Chat checkpoint management...")
        
        # Create a session for demonstration
        session_id = client.create_session()
        print(f"Created session: {session_id}")
        
        # Send some messages to create history
        await client.chat("Hello, how are you?", session_id)
        await client.chat("What's the weather like?", session_id)
        
        # Save checkpoint
        save_result = await client.chat_save_checkpoint("demo_checkpoint", session_id)
        print(f"Save checkpoint: {save_result}")
        
        # List checkpoints
        list_result = await client.chat_list_checkpoints()
        print(f"List checkpoints: {list_result}")
        
        # 5. Demonstrate extension management
        print("\n5. Extension management...")
        ext_list_result = await client.manage_extensions("list")
        print(f"Extensions list: {ext_list_result}")
        
        # 6. Demonstrate MCP server management
        print("\n6. MCP server management...")
        mcp_list_result = await client.manage_mcp_servers("list")
        print(f"MCP servers: {mcp_list_result}")
        
        # 7. Demonstrate workspace directory management
        print("\n7. Workspace directory management...")
        dir_show_result = await client.manage_workspace_directories("show")
        print(f"Workspace directories: {dir_show_result}")
        
        # 8. Demonstrate memory management
        print("\n8. Memory management...")
        memory_show_result = await client.manage_memory("show")
        print(f"Memory contents: {memory_show_result}")
        
        # 9. List available tools
        print("\n9. Available tools...")
        tools_result = await client.list_tools(show_descriptions=True)
        print(f"Tools: {tools_result}")
        
        # 10. Demonstrate advanced message sending with system commands
        print("\n10. Advanced message sending with system commands...")
        
        # Send a system command through message interface
        system_cmd_response = await client.send_message_with_features("/help")
        print(f"System command response: {system_cmd_response.content}")
        print(f"Metadata: {system_cmd_response.metadata}")
        
        # 11. Demonstrate direct system command execution
        print("\n11. Direct system command execution...")
        
        # Execute various system commands
        commands_to_test = [
            ("clear", []),
            ("stats", ["general"]),
            ("memory", ["show"]),
            ("tools", []),
            ("extensions", ["list"])
        ]
        
        for cmd, args in commands_to_test:
            try:
                result = await client.execute_system_command(cmd, args)
                print(f"/{cmd} {' '.join(args)}: {result.get('success', False)}")
                if result.get('message'):
                    print(f"  Message: {result['message']}")
            except Exception as e:
                print(f"/{cmd} failed: {e}")
        
        # 12. Clean up
        print("\n12. Cleanup...")
        client.close_session(session_id)
        print("Session closed")
        
        print("\n=== Demo completed ===")


async def interactive_system_commands():
    """Interactive system commands demo."""
    
    async with GeminiClient() as client:
        print("=== Interactive System Commands Demo ===")
        print("Type system commands (starting with /) or 'quit' to exit")
        print("Examples: /help, /about, /stats, /clear")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    # Parse command and arguments
                    parts = user_input[1:].split()
                    command = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    
                    try:
                        result = await client.execute_system_command(command, args)
                        print(f"Result: {result}")
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    # Regular message
                    response = await client.one_shot(user_input)
                    print(f"Gemini: {response}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Goodbye!")


if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Automated demo")
    print("2. Interactive demo")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(interactive_system_commands())
    else:
        asyncio.run(main())
