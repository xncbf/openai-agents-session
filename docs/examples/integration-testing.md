# Integration Testing

This guide shows how to test your application with real Redis and DynamoDB backends using Docker.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.10+

## Project Structure

The `examples/` directory in the repository contains everything you need:

```
examples/
├── docker-compose.yml      # Redis + DynamoDB Local
├── test_redis_session.py   # Redis integration test
├── test_dynamodb_session.py # DynamoDB integration test
└── test_with_agent.py      # OpenAI Agent integration test
```

## Starting Services

```bash
cd examples
docker compose up -d
```

This starts:

- **Redis** on port 6379
- **DynamoDB Local** on port 8000

## Running Tests

### Redis Test

```bash
uv run python test_redis_session.py
```

```python
"""Test RedisSession with actual Redis."""

import asyncio
import redis.asyncio as redis
from openai_agents_session import RedisSession


async def main():
    print("Testing RedisSession with actual Redis")

    client = redis.from_url("redis://localhost:6379")
    session = RedisSession(
        session_id="test-session-001",
        redis_client=client,
        ttl=300,
    )

    # Clear any existing data
    await session.clear_session()
    print("[1] Cleared existing session data")

    # Add items
    items = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well!"},
    ]
    await session.add_items(items)
    print(f"[2] Added {len(items)} items")

    # Get all items
    retrieved = await session.get_items()
    print(f"[3] Retrieved {len(retrieved)} items")

    # Check TTL
    ttl = await client.ttl(session._key)
    print(f"[4] TTL remaining: {ttl} seconds")

    await client.aclose()
    print("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

### DynamoDB Test

```bash
uv run python test_dynamodb_session.py
```

```python
"""Test DynamoDBSession with actual DynamoDB Local."""

import asyncio
from aiobotocore.session import get_session
from openai_agents_session import DynamoDBSession

TABLE_NAME = "agent_sessions"


async def create_table(client) -> None:
    """Create the DynamoDB table if it doesn't exist."""
    try:
        await client.describe_table(TableName=TABLE_NAME)
    except client.exceptions.ResourceNotFoundException:
        await client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "session_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        waiter = client.get_waiter("table_exists")
        await waiter.wait(TableName=TABLE_NAME)


async def main():
    print("Testing DynamoDBSession with DynamoDB Local")

    boto_session = get_session()
    async with boto_session.create_client(
        "dynamodb",
        region_name="us-east-1",
        endpoint_url="http://localhost:8000",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    ) as client:
        await create_table(client)

        session = DynamoDBSession(
            session_id="test-session-001",
            dynamodb_client=client,
            table_name=TABLE_NAME,
            ttl_seconds=300,
        )

        await session.clear_session()
        print("[1] Cleared existing session data")

        items = [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        await session.add_items(items)
        print(f"[2] Added {len(items)} items")

        retrieved = await session.get_items()
        print(f"[3] Retrieved {len(retrieved)} items")

    print("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

### Agent Integration Test

Requires `OPENAI_API_KEY`:

```bash
export OPENAI_API_KEY=your-api-key
uv run python test_with_agent.py
```

## Docker Compose Configuration

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  dynamodb:
    image: amazon/dynamodb-local:latest
    ports:
      - "8000:8000"
    command: "-jar DynamoDBLocal.jar -sharedDb -inMemory"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:8000 || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 5
```

## pytest Integration

For automated testing with pytest:

```python
# conftest.py
import pytest
import redis.asyncio as redis
from openai_agents_session import RedisSession


@pytest.fixture
async def redis_client():
    client = redis.from_url("redis://localhost:6379")
    yield client
    await client.aclose()


@pytest.fixture
async def redis_session(redis_client):
    session = RedisSession(
        session_id="test-session",
        redis_client=redis_client,
    )
    yield session
    await session.clear_session()


# test_session.py
import pytest


@pytest.mark.asyncio
async def test_add_and_get_items(redis_session):
    items = [{"role": "user", "content": "Hello"}]
    await redis_session.add_items(items)

    retrieved = await redis_session.get_items()
    assert len(retrieved) == 1
    assert retrieved[0]["content"] == "Hello"
```

## Cleanup

```bash
docker compose down
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

      dynamodb:
        image: amazon/dynamodb-local:latest
        ports:
          - 8000:8000

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install ".[all,dev]"

      - name: Run integration tests
        run: pytest tests/integration/
```
