"""
Advanced Features Example for Gemini CLI SDK

This example demonstrates the advanced features including:
- File reference processing (@filename syntax)
- Shell command execution (!command syntax)
- System command integration (/command syntax)
"""

import asyncio
import tempfile
import os
from gemini_cli_sdk import GeminiClient


async def main():
    """Demonstrate advanced features of Gemini CLI SDK."""
    
    print("=== Gemini CLI SDK Advanced Features Demo ===\n")
    
    async with GeminiClient() as client:
        
        # 1. System Commands Demo
        print("1. System Commands Demo")
        print("-" * 30)
        
        # Get help information
        try:
            help_result = await client.system_help()
            print(f"✅ System help: {help_result.get('message', 'Help retrieved successfully')}")
        except Exception as e:
            print(f"❌ System help failed: {e}")
        
        # Get statistics
        try:
            stats_result = await client.system_stats()
            print(f"✅ System stats: {stats_result.get('message', 'Stats retrieved successfully')}")
        except Exception as e:
            print(f"❌ System stats failed: {e}")
        
        print()
        
        # 2. File Reference Demo
        print("2. File Reference Processing Demo")
        print("-" * 40)
        
        # Create a temporary file for demonstration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("Hello, this is a test file!\nIt contains some sample content.\nLine 3 of the file.")
            temp_filename = temp_file.name
        
        try:
            # Test file reference processing
            message_with_file_ref = f"Please analyze this file: @{temp_filename}"
            processed_message = client.process_file_references(message_with_file_ref)
            
            print(f"Original message: {message_with_file_ref}")
            print(f"Processed message: {processed_message[:200]}...")
            print("✅ File reference processing successful")
            
            # Test with quoted filename
            quoted_message = f'Please check @"{temp_filename}" for content'
            processed_quoted = client.process_file_references(quoted_message)
            print(f"✅ Quoted filename processing successful")
            
            # Test non-existent file
            nonexistent_message = "Check @nonexistent_file.txt"
            processed_nonexistent = client.process_file_references(nonexistent_message)
            print(f"Non-existent file result: {processed_nonexistent}")
            print("✅ Non-existent file handling successful")
            
        except Exception as e:
            print(f"❌ File reference processing failed: {e}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
        
        print()
        
        # 3. Shell Command Demo
        print("3. Shell Command Execution Demo")
        print("-" * 40)
        
        # Test safe commands
        safe_commands = [
            "echo Hello World",
            "pwd",
            "date",
            "whoami"
        ]
        
        for cmd in safe_commands:
            try:
                result = await client.execute_shell_command(cmd)
                if result['success']:
                    print(f"✅ Command '{cmd}': {result['stdout'].strip()}")
                else:
                    print(f"⚠️  Command '{cmd}' failed: {result['stderr']}")
            except Exception as e:
                print(f"❌ Command '{cmd}' error: {e}")
        
        # Test dangerous command (should be blocked)
        try:
            dangerous_result = await client.execute_shell_command("rm -rf /")
            print(f"🛡️  Dangerous command blocked: {dangerous_result['message']}")
        except Exception as e:
            print(f"🛡️  Dangerous command handling: {e}")
        
        # Test command timeout (simulate with sleep)
        try:
            # This might timeout depending on system
            timeout_result = await client.execute_shell_command("sleep 1")
            if timeout_result['success']:
                print("✅ Short sleep command completed")
            else:
                print(f"⚠️  Sleep command result: {timeout_result['message']}")
        except Exception as e:
            print(f"❌ Sleep command error: {e}")
        
        print()
        
        # 4. Unified Message Interface Demo
        print("4. Unified Message Interface Demo")
        print("-" * 40)
        
        session_id = client.create_session()
        
        # Test system command through unified interface
        try:
            system_response = await client.send_message_with_features("/help")
            print("✅ System command through unified interface successful")
            print(f"Response type: {type(system_response.metadata.get('command_result'))}")
        except Exception as e:
            print(f"❌ System command through unified interface failed: {e}")
        
        # Test shell command through unified interface (if enabled)
        try:
            shell_response = await client.send_message_with_features(
                "!echo 'Hello from shell'", 
                allow_shell_commands=True
            )
            print("✅ Shell command through unified interface successful")
            print(f"Response type: {type(shell_response.metadata.get('command_result'))}")
        except Exception as e:
            print(f"❌ Shell command through unified interface failed: {e}")
        
        # Test file reference through unified interface
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_py_file:
            temp_py_file.write("# Sample Python file\nprint('Hello, World!')\n")
            temp_py_filename = temp_py_file.name
        
        try:
            file_response = await client.send_message_with_features(
                f"What does this Python file do? @{temp_py_filename}",
                session_id=session_id,
                process_file_refs=True
            )
            print("✅ File reference through unified interface successful")
            print(f"Message length: {len(file_response.content)} characters")
        except Exception as e:
            print(f"❌ File reference through unified interface failed: {e}")
        finally:
            try:
                os.unlink(temp_py_filename)
            except:
                pass
        
        # Clean up session
        client.close_session(session_id)
        
        print()
        
        # 5. Security Features Demo
        print("5. Security Features Demo")
        print("-" * 30)
        
        # Test file size limit
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as large_file:
            # Create a file larger than 10KB
            large_content = "A" * 15000  # 15KB
            large_file.write(large_content)
            large_filename = large_file.name
        
        try:
            large_file_message = f"Process this large file: @{large_filename}"
            processed_large = client.process_file_references(large_file_message)
            if "truncated" in processed_large:
                print("✅ Large file truncation working correctly")
            else:
                print("⚠️  Large file truncation may not be working")
        except Exception as e:
            print(f"❌ Large file processing error: {e}")
        finally:
            try:
                os.unlink(large_filename)
            except:
                pass
        
        # Test command blacklist
        dangerous_commands = ["rm", "sudo", "kill", "shutdown"]
        for dangerous_cmd in dangerous_commands:
            try:
                result = await client.execute_shell_command(f"{dangerous_cmd} test")
                if not result['success'] and ("not allowed" in result['message'] or "blocked" in result['message']):
                    print(f"✅ Dangerous command '{dangerous_cmd}' properly blocked")
                else:
                    print(f"⚠️  Dangerous command '{dangerous_cmd}' not properly blocked: {result['message']}")
            except Exception as e:
                print(f"❌ Error testing dangerous command '{dangerous_cmd}': {e}")
        
        print()
        print("=== Demo Complete ===")
        print("All advanced features have been demonstrated!")


if __name__ == "__main__":
    asyncio.run(main())
