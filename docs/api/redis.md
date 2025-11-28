# RedisSession

Redis-based session storage for openai-agents.

## Class Definition

::: openai_agents_session.redis.RedisSession
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get_items
        - add_items
        - pop_item
        - clear_session

## Usage Example

```python
import redis.asyncio as redis
from openai_agents_session import RedisSession

# Create client
client = redis.from_url("redis://localhost:6379")

# Create session
session = RedisSession(
    session_id="user-123",
    redis_client=client,
    key_prefix="myapp:sessions",
    ttl=3600,
)

# Add items
await session.add_items([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
])

# Get items
items = await session.get_items()
# [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]

# Get limited items
recent = await session.get_items(limit=1)
# [{"role": "assistant", "content": "Hi there!"}]

# Pop last item
last = await session.pop_item()
# {"role": "assistant", "content": "Hi there!"}

# Clear session
await session.clear_session()
```

## Parameters

### session_id

- **Type**: `str`
- **Required**: Yes

Unique identifier for the session. Used as part of the Redis key.

### redis_client

- **Type**: `Redis[bytes]`
- **Required**: Yes

An async Redis client instance from `redis.asyncio`.

### key_prefix

- **Type**: `str`
- **Default**: `"openai_agents_session"`

Prefix for Redis keys. The full key format is `{key_prefix}:{session_id}`.

### ttl

- **Type**: `int | None`
- **Default**: `None`

Time-to-live in seconds. If set, the key will expire after this duration. The TTL is refreshed on every `add_items()` call.

## Methods

### get_items

```python
async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]
```

Retrieve conversation history.

**Parameters:**

- `limit`: Maximum number of items to return. Returns the most recent items.

**Returns:** List of conversation items in chronological order.

### add_items

```python
async def add_items(self, items: list[TResponseInputItem]) -> None
```

Add new items to the conversation history.

**Parameters:**

- `items`: List of items to add.

### pop_item

```python
async def pop_item(self) -> TResponseInputItem | None
```

Remove and return the most recent item.

**Returns:** The removed item, or `None` if the session is empty.

### clear_session

```python
async def clear_session(self) -> None
```

Delete all items in the session.

## Redis Key Structure

Keys are stored as Redis lists:

```
Key: {key_prefix}:{session_id}
Type: List
Value: [JSON item 1, JSON item 2, ...]
```

## See Also

- [Redis Backend Guide](../backends/redis.md)
- [Quick Start](../getting-started/quickstart.md)
