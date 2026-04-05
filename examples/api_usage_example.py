"""
API Usage Example for Gemini CLI SDK

Demonstrates how to use the OpenAI-compatible API
"""

import asyncio
from openai import OpenAI, AsyncOpenAI


def basic_chat_example():
    """Basic chat completion example (non-streaming)"""
    print("=" * 60)
    print("Basic Chat Completion Example")
    print("=" * 60)

    # Initialize OpenAI client pointing to local Gemini API
    client = OpenAI(
        base_url='http://localhost:8765/v1',
        api_key='dummy-key'  # API key is not required but OpenAI SDK needs it
    )

    # Send a chat completion request
    response = client.chat.completions.create(
        model='gemini-2.5-pro',
        messages=[
            {'role': 'user', 'content': 'What is the capital of France?'}
        ],
    )

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Model: {response.model}")
    print(f"Finish Reason: {response.choices[0].finish_reason}")
    if response.usage:
        print(f"Tokens: {response.usage.total_tokens}")
    print()


def streaming_chat_example():
    """Streaming chat completion example"""
    print("=" * 60)
    print("Streaming Chat Completion Example")
    print("=" * 60)

    client = OpenAI(
        base_url='http://localhost:8765/v1',
        api_key='dummy-key'
    )

    # Send a streaming chat completion request
    stream = client.chat.completions.create(
        model='gemini-2.5-flash',
        messages=[
            {'role': 'user', 'content': 'Write a short poem about Python programming'}
        ],
        stream=True
    )

    print("Streaming response:")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='', flush=True)
    print("\n")


def conversation_example():
    """Multi-turn conversation example"""
    print("=" * 60)
    print("Multi-turn Conversation Example")
    print("=" * 60)

    client = OpenAI(
        base_url='http://localhost:8765/v1',
        api_key='dummy-key'
    )

    # Maintain conversation history
    messages = [
        {'role': 'system', 'content': 'You are a helpful programming assistant.'},
        {'role': 'user', 'content': 'What is Python?'}
    ]

    # First exchange
    response = client.chat.completions.create(
        model='gemini-2.5-pro',
        messages=messages
    )
    assistant_response = response.choices[0].message.content
    print(f"User: {messages[-1]['content']}")
    print(f"Assistant: {assistant_response}\n")

    # Add to conversation history
    messages.append({'role': 'assistant', 'content': assistant_response})

    # Second exchange
    messages.append({'role': 'user', 'content': 'Can you give me an example?'})
    response = client.chat.completions.create(
        model='gemini-2.5-pro',
        messages=messages
    )
    assistant_response = response.choices[0].message.content
    print(f"User: {messages[-1]['content']}")
    print(f"Assistant: {assistant_response}\n")


async def async_example():
    """Async API usage example"""
    print("=" * 60)
    print("Async API Usage Example")
    print("=" * 60)

    client = AsyncOpenAI(
        base_url='http://localhost:8765/v1',
        api_key='dummy-key'
    )

    # Send async request
    response = await client.chat.completions.create(
        model='gemini-2.5-flash',
        messages=[
            {'role': 'user', 'content': 'What is async programming?'}
        ],
    )

    print(f"Response: {response.choices[0].message.content}\n")


async def concurrent_requests_example():
    """Multiple concurrent requests example"""
    print("=" * 60)
    print("Concurrent Requests Example")
    print("=" * 60)

    client = AsyncOpenAI(
        base_url='http://localhost:8765/v1',
        api_key='dummy-key'
    )

    # Define multiple questions
    questions = [
        "What is machine learning?",
        "What is deep learning?",
        "What is natural language processing?"
    ]

    # Create tasks for concurrent execution
    tasks = []
    for question in questions:
        task = client.chat.completions.create(
            model='gemini-2.5-flash',
            messages=[{'role': 'user', 'content': question}]
        )
        tasks.append(task)

    # Execute all requests concurrently
    responses = await asyncio.gather(*tasks)

    # Display results
    for question, response in zip(questions, responses):
        print(f"Q: {question}")
        print(f"A: {response.choices[0].message.content[:100]}...\n")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Gemini CLI SDK API Usage Examples")
    print("=" * 60 + "\n")
    print("Make sure the API server is running:")
    print("  gemini-api-server --port 8765\n")
    print("=" * 60 + "\n")

    # Run synchronous examples
    try:
        basic_chat_example()
        streaming_chat_example()
        conversation_example()

        # Run async examples
        asyncio.run(async_example())
        asyncio.run(concurrent_requests_example())

        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nPlease make sure:")
        print("1. The API server is running (gemini-api-server)")
        print("2. You have installed the OpenAI SDK (pip install openai)")
        print("3. Gemini CLI is properly configured")


if __name__ == "__main__":
    main()
