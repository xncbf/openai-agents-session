# Quick Start

This guide will help you create your first AI agent with persistent memory in under 5 minutes.

## Prerequisites

- Python 3.10+
- Redis or DynamoDB running locally
- OpenAI API key

## Step 1: Install the Package

```bash
pip install "openai-agents-session[redis]"
```

## Step 2: Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

## Step 3: Set Your API Key

```bash
export OPENAI_API_KEY=your-api-key
```

## Step 4: Create Your Agent

```python
import asyncio
import redis.asyncio as redis
from agents import Agent, Runner
from openai_agents_session import RedisSession


async def main():
    # Connect to Redis
    client = redis.from_url("redis://localhost:6379")

    # Create a session for this user
    session = RedisSession(
        session_id="user-alice-123",
        redis_client=client,
        ttl=3600,  # 1 hour expiration
    )

    # Create your agent
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant. Remember details about the user.",
    )

    # Create runner with session
    runner = Runner(agent=agent, session=session)

    # First conversation
    print("User: Hi! My name is Alice and I love Python.")
    result = await runner.run("Hi! My name is Alice and I love Python.")
    print(f"Assistant: {result.final_output}\n")

    # Second conversation - agent remembers!
    print("User: What's my name and what do I love?")
    result = await runner.run("What's my name and what do I love?")
    print(f"Assistant: {result.final_output}\n")

    # Check stored history
    items = await session.get_items()
    print(f"Session contains {len(items)} messages")

    # Cleanup
    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Step 5: Run It!

```bash
python your_script.py
```

Expected output:

```
User: Hi! My name is Alice and I love Python.
Assistant: Hello Alice! It's great to meet you. Python is a fantastic programming language...

User: What's my name and what do I love?
Assistant: Your name is Alice and you love Python!

Session contains 4 messages
```

## Understanding Sessions

### Session ID

The `session_id` uniquely identifies a conversation. Use it to:

- Track individual users: `session_id="user-{user_id}"`
- Track conversations: `session_id="conv-{conversation_id}"`
- Combine both: `session_id="user-{user_id}-conv-{conv_id}"`

```python
# Per-user sessions
session = RedisSession(
    session_id=f"user-{user.id}",
    redis_client=client,
)

# Per-conversation sessions
session = RedisSession(
    session_id=f"conversation-{conv_id}",
    redis_client=client,
)
```

### TTL (Time To Live)

Set automatic expiration for sessions:

```python
# Expire after 1 hour
session = RedisSession(session_id="...", redis_client=client, ttl=3600)

# Expire after 24 hours
session = RedisSession(session_id="...", redis_client=client, ttl=86400)

# Never expire (default)
session = RedisSession(session_id="...", redis_client=client, ttl=None)
```

### Managing Session Data

```python
# Get all messages
messages = await session.get_items()

# Get last N messages
recent = await session.get_items(limit=10)

# Remove last message
removed = await session.pop_item()

# Clear entire session
await session.clear_session()
```

## Using with DynamoDB

The DynamoDB backend works similarly:

```python
from aiobotocore.session import get_session
from openai_agents_session import DynamoDBSession

async def main():
    boto_session = get_session()
    async with boto_session.create_client(
        "dynamodb",
        region_name="us-east-1",
    ) as client:
        session = DynamoDBSession(
            session_id="user-alice-123",
            dynamodb_client=client,
            table_name="agent_sessions",
            ttl_seconds=3600,
        )

        # Use with your agent...
```

## Next Steps

- [Redis Backend](../backends/redis.md) - Advanced Redis configuration
- [DynamoDB Backend](../backends/dynamodb.md) - AWS setup and IAM policies
- [API Reference](../api/index.md) - Complete API documentation
