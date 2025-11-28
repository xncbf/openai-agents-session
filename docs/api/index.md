# API Reference

This section provides detailed API documentation for all classes and functions in `openai-agents-session`.

## Session Backends

Both session backends implement the `SessionABC` interface from `openai-agents-python`:

| Class | Backend | Import |
|-------|---------|--------|
| [RedisSession](redis.md) | Redis | `from openai_agents_session import RedisSession` |
| [DynamoDBSession](dynamodb.md) | AWS DynamoDB | `from openai_agents_session import DynamoDBSession` |

## SessionABC Interface

All session backends implement this interface:

```python
from abc import ABC, abstractmethod
from typing import Any

class SessionABC(ABC):
    @abstractmethod
    async def get_items(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get conversation items, optionally limited to the last N items."""
        ...

    @abstractmethod
    async def add_items(self, items: list[dict[str, Any]]) -> None:
        """Add new items to the conversation history."""
        ...

    @abstractmethod
    async def pop_item(self) -> dict[str, Any] | None:
        """Remove and return the most recent item."""
        ...

    @abstractmethod
    async def clear_session(self) -> None:
        """Clear all items from the session."""
        ...
```

## Common Parameters

### session_id

All backends require a `session_id` parameter:

```python
session = RedisSession(
    session_id="user-123-conv-456",  # Unique identifier
    ...
)
```

**Best practices for session IDs:**

- Include user identifier: `f"user-{user_id}"`
- Include conversation ID: `f"conv-{conv_id}"`
- Include context: `f"user-{user_id}-agent-{agent_name}"`

### TTL / ttl_seconds

Control automatic expiration:

```python
# Redis uses `ttl` (seconds)
redis_session = RedisSession(session_id="...", redis_client=client, ttl=3600)

# DynamoDB uses `ttl_seconds`
dynamo_session = DynamoDBSession(
    session_id="...",
    dynamodb_client=client,
    table_name="sessions",
    ttl_seconds=3600,
)
```

## Type Hints

The library exports type information (PEP 561 compliant):

```python
from openai_agents_session import RedisSession, DynamoDBSession

# Type checkers understand these types
def create_session(backend: str) -> RedisSession | DynamoDBSession:
    ...
```

## Lazy Loading

Backends are lazily loaded to avoid importing unnecessary dependencies:

```python
# Only imports redis when accessed
from openai_agents_session import RedisSession

# Only imports aiobotocore when accessed
from openai_agents_session import DynamoDBSession

# ImportError if dependency not installed
from openai_agents_session import RedisSession
# ImportError: RedisSession requires the 'redis' extra.
# Install it with: pip install 'openai-agents-session[redis]'
```

## Error Handling

```python
from openai_agents_session import RedisSession
import redis.asyncio as redis

async def safe_operation():
    try:
        items = await session.get_items()
    except redis.ConnectionError:
        # Handle connection failure
        pass
    except redis.TimeoutError:
        # Handle timeout
        pass
```
