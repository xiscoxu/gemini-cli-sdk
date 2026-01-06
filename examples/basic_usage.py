"""Basic usage examples for Gemini CLI SDK."""

import asyncio
from gemini_cli_sdk import GeminiClient


async def simple_query():
    """Simple one-shot query example."""
    print("=== Simple Query Example ===")
    
    async with GeminiClient() as client:
        response = await client.one_shot("What is Python programming language?")
        print(f"Response: {response}")


async def session_conversation():
    """Session-based conversation example."""
    print("\n=== Session Conversation Example ===")
    
    async with GeminiClient() as client:
        # Create a session for contextual conversation
        session_id = client.create_session()
        print(f"Created session: {session_id}")
        
        # Have a conversation
        questions = [
            "Hello, I'm learning programming",
            "Can you explain what variables are?",
            "How do I create a variable in Python?",
            "What's the difference between strings and numbers?"
        ]
        
        for question in questions:
            print(f"\nUser: {question}")
            response = await client.chat(question, session_id)
            print(f"AI: {response}")
        
        # Get session info
        session_info = client.get_session_info(session_id)
        print(f"\nSession info: {session_info.message_count} messages exchanged")
        
        # Clean up
        client.close_session(session_id)


async def system_instruction_example():
    """Example using system instructions."""
    print("\n=== System Instruction Example ===")
    
    async with GeminiClient() as client:
        system_instruction = (
            "You are a helpful Python programming tutor. "
            "Provide clear, beginner-friendly explanations with simple examples."
        )
        
        response = await client.one_shot(
            "How do I create a function in Python?",
            system_instruction=system_instruction
        )
        print(f"Response: {response}")


async def batch_processing():
    """Batch processing example."""
    print("\n=== Batch Processing Example ===")
    
    async with GeminiClient() as client:
        session_id = client.create_session()
        
        questions = [
            "What is machine learning?",
            "What are the main types of machine learning?",
            "Can you give me a simple example?"
        ]
        
        print("Sending batch of questions...")
        responses = await client.send_batch(questions, session_id)
        
        for i, (question, response) in enumerate(zip(questions, responses), 1):
            print(f"\nQ{i}: {question}")
            print(f"A{i}: {response.content}")
        
        client.close_session(session_id)


async def concurrent_processing():
    """Concurrent processing example."""
    print("\n=== Concurrent Processing Example ===")
    
    async with GeminiClient() as client:
        questions = [
            "What is Python?",
            "What is JavaScript?",
            "What is Go programming language?",
            "What is Rust?"
        ]
        
        print("Sending questions concurrently...")
        responses = await client.send_concurrent(questions)
        
        for question, response in zip(questions, responses):
            print(f"\nQ: {question}")
            print(f"A: {response.content[:100]}...")  # Truncate for display


async def client_stats():
    """Client statistics example."""
    print("\n=== Client Statistics Example ===")
    
    async with GeminiClient() as client:
        # Create some sessions and send messages
        session1 = client.create_session()
        session2 = client.create_session()
        
        await client.chat("Hello", session1)
        await client.chat("Hi there", session2)
        
        # Get statistics
        stats = client.get_stats()
        print("Client Statistics:")
        print(f"  Started: {stats['started']}")
        print(f"  Total sessions: {stats['sessions']['total']}")
        print(f"  Active sessions: {stats['sessions']['active']}")
        print(f"  Total processes: {stats['processes']['total']}")
        print(f"  Idle processes: {stats['processes']['idle']}")
        print(f"  Max processes: {stats['processes']['max']}")
        
        # Health check
        health = await client.health_check()
        print(f"\nHealth Status: {health['status']}")
        
        # Clean up
        client.close_session(session1)
        client.close_session(session2)


async def main():
    """Run all examples."""
    try:
        await simple_query()
        await session_conversation()
        await system_instruction_example()
        await batch_processing()
        await concurrent_processing()
        await client_stats()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure Gemini CLI is installed and available in PATH")


if __name__ == "__main__":
    asyncio.run(main())
