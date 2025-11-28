# openai-agents-session

[![PyPI version](https://badge.fury.io/py/openai-agents-session.svg)](https://badge.fury.io/py/openai-agents-session)
[![CI](https://github.com/xncbf/openai-agents-session/actions/workflows/ci.yml/badge.svg)](https://github.com/xncbf/openai-agents-session/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/xncbf/openai-agents-session/graph/badge.svg)](https://codecov.io/gh/xncbf/openai-agents-session)
[![Python versions](https://img.shields.io/pypi/pyversions/openai-agents-session.svg)](https://pypi.org/project/openai-agents-session/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Redis and DynamoDB session backends for [openai-agents-python](https://github.com/openai/openai-agents-python).

## Installation

Install with your preferred backend:

```bash
# Redis only
pip install "openai-agents-session[redis]"

# DynamoDB only
pip install "openai-agents-session[dynamodb]"

# Both backends
pip install "openai-agents-session[all]"
```

## Quick Start

### Redis Session

```python
import redis.asyncio as redis
from agents import Agent, Runner
from openai_agents_session import RedisSession

# Create Redis client
client = redis.from_url("redis://localhost:6379")

# Create session with optional TTL
session = RedisSession(
    session_id="user-123",
    redis_client=client,
    ttl=3600,  # 1 hour expiration
)

# Use with openai-agents
agent = Agent(name="Assistant", instructions="You are a helpful assistant.")
runner = Runner(agent=agent, session=session)

# Run conversation
result = await runner.run("Hello!")
print(result.final_output)

# Continue the conversation (history is preserved)
result = await runner.run("What did I just say?")
print(result.final_output)
```

### DynamoDB Session

```python
from aiobotocore.session import get_session
from agents import Agent, Runner
from openai_agents_session import DynamoDBSession

# Create DynamoDB client
boto_session = get_session()
async with boto_session.create_client("dynamodb", region_name="us-east-1") as client:
    # Create session
    session = DynamoDBSession(
        session_id="user-123",
        dynamodb_client=client,
        table_name="agent_sessions",
        ttl_seconds=3600,  # 1 hour expiration
    )

    # Use with openai-agents
    agent = Agent(name="Assistant", instructions="You are a helpful assistant.")
    runner = Runner(agent=agent, session=session)

    result = await runner.run("Hello!")
    print(result.final_output)
```

## DynamoDB Table Setup

Create a DynamoDB table with the following schema:

| Attribute | Type | Key |
|-----------|------|-----|
| session_id | String | Partition Key |

For TTL support, enable Time to Live with attribute name `ttl`.

### Using AWS CLI

```bash
aws dynamodb create-table \
    --table-name agent_sessions \
    --attribute-definitions AttributeName=session_id,AttributeType=S \
    --key-schema AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Enable TTL
aws dynamodb update-time-to-live \
    --table-name agent_sessions \
    --time-to-live-specification Enabled=true,AttributeName=ttl
```

### Using Helper Function (Development Only)

```python
from openai_agents_session.dynamodb import create_table_if_not_exists

await create_table_if_not_exists(client, "agent_sessions", enable_ttl=True)
```

## API Reference

### RedisSession

```python
RedisSession(
    session_id: str,           # Unique session identifier
    redis_client: Redis,       # Async Redis client
    key_prefix: str = "openai_agents_session",  # Redis key prefix
    ttl: int | None = None,    # TTL in seconds (None = no expiration)
)
```

### DynamoDBSession

```python
DynamoDBSession(
    session_id: str,           # Unique session identifier
    dynamodb_client: DynamoDBClient,  # aiobotocore DynamoDB client
    table_name: str,           # DynamoDB table name
    ttl_seconds: int | None = None,   # TTL in seconds (None = no expiration)
)
```

### Common Methods (SessionABC)

| Method | Description |
|--------|-------------|
| `get_items(limit=None)` | Get conversation history (most recent `limit` items) |
| `add_items(items)` | Add items to conversation history |
| `pop_item()` | Remove and return the most recent item |
| `clear_session()` | Delete all items in the session |

## Development

```bash
# Clone the repository
git clone https://github.com/xncbf/openai-agents-session.git
cd openai-agents-session

# Install dependencies
uv sync --all-extras

# Run linter
uv run ruff check .

# Run formatter
uv run ruff format .

# Run type checker
uv run ty check src/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.
