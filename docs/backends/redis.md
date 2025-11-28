# Redis Backend

The Redis backend provides high-performance, in-memory session storage with optional persistence and automatic expiration.

## Overview

Redis is ideal for:

- **Low latency** - Sub-millisecond response times
- **High throughput** - Handles thousands of operations per second
- **Simplicity** - Easy to set up and operate
- **Caching scenarios** - When session data can be regenerated

## Installation

```bash
pip install "openai-agents-session[redis]"
```

## Basic Usage

```python
import redis.asyncio as redis
from openai_agents_session import RedisSession

# Create Redis client
client = redis.from_url("redis://localhost:6379")

# Create session
session = RedisSession(
    session_id="user-123",
    redis_client=client,
    ttl=3600,  # Optional: expire after 1 hour
)
```

## Configuration Options

### RedisSession Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | `str` | Required | Unique identifier for the session |
| `redis_client` | `Redis[bytes]` | Required | Async Redis client instance |
| `key_prefix` | `str` | `"openai_agents_session"` | Prefix for Redis keys |
| `ttl` | `int \| None` | `None` | Time-to-live in seconds |

### Key Prefix

The key prefix helps organize keys in Redis:

```python
# Default: keys like "openai_agents_session:user-123"
session = RedisSession(
    session_id="user-123",
    redis_client=client,
)

# Custom prefix: keys like "myapp:sessions:user-123"
session = RedisSession(
    session_id="user-123",
    redis_client=client,
    key_prefix="myapp:sessions",
)
```

### TTL (Time To Live)

```python
# Expire after 1 hour
session = RedisSession(session_id="...", redis_client=client, ttl=3600)

# Expire after 7 days
session = RedisSession(session_id="...", redis_client=client, ttl=604800)

# Never expire
session = RedisSession(session_id="...", redis_client=client, ttl=None)
```

!!! warning "TTL Refresh"
    The TTL is refreshed every time you call `add_items()`. This means active sessions won't expire unexpectedly.

## Redis Client Configuration

### Connection URL

```python
# Local Redis
client = redis.from_url("redis://localhost:6379")

# With password
client = redis.from_url("redis://:password@localhost:6379")

# With database selection
client = redis.from_url("redis://localhost:6379/1")

# SSL/TLS connection
client = redis.from_url("rediss://localhost:6379")
```

### Connection Pool

For production, configure the connection pool:

```python
client = redis.from_url(
    "redis://localhost:6379",
    max_connections=50,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
    retry_on_timeout=True,
)
```

### Cluster Mode

```python
from redis.asyncio.cluster import RedisCluster

client = RedisCluster.from_url("redis://localhost:6379")
session = RedisSession(
    session_id="user-123",
    redis_client=client,  # Works with cluster client
)
```

## Data Storage Format

Sessions are stored as Redis lists with JSON-serialized items:

```
Key: openai_agents_session:user-123
Type: List
Value: [
    '{"role": "user", "content": "Hello"}',
    '{"role": "assistant", "content": "Hi there!"}'
]
```

## Operations

### Get Items

```python
# Get all items
items = await session.get_items()

# Get last 10 items (most recent)
recent = await session.get_items(limit=10)
```

### Add Items

```python
# Add single item
await session.add_items([{"role": "user", "content": "Hello"}])

# Add multiple items
await session.add_items([
    {"role": "user", "content": "What's 2+2?"},
    {"role": "assistant", "content": "4"},
])
```

### Pop Item

```python
# Remove and return the most recent item
last_item = await session.pop_item()
if last_item:
    print(f"Removed: {last_item['content']}")
```

### Clear Session

```python
# Delete entire session
await session.clear_session()
```

## Production Deployment

### Redis Sentinel (High Availability)

```python
from redis.asyncio.sentinel import Sentinel

sentinel = Sentinel(
    [("sentinel1", 26379), ("sentinel2", 26379), ("sentinel3", 26379)],
    socket_timeout=0.5,
)
client = sentinel.master_for("mymaster")

session = RedisSession(session_id="user-123", redis_client=client)
```

### AWS ElastiCache

```python
client = redis.from_url(
    "rediss://my-cluster.abc123.use1.cache.amazonaws.com:6379",
    ssl_cert_reqs="required",
)
```

### Redis Cloud

```python
client = redis.from_url(
    "rediss://default:password@redis-12345.c1.us-east-1-2.ec2.cloud.redislabs.com:12345"
)
```

## Monitoring

### Check Key Existence

```python
exists = await client.exists(session._key)
```

### Get TTL

```python
ttl_remaining = await client.ttl(session._key)
print(f"Session expires in {ttl_remaining} seconds")
```

### Memory Usage

```python
memory = await client.memory_usage(session._key)
print(f"Session uses {memory} bytes")
```

## Best Practices

1. **Use appropriate TTLs** - Set TTL based on your use case to prevent memory bloat
2. **Use connection pooling** - Reuse connections instead of creating new ones
3. **Handle connection errors** - Redis connections can fail; implement retry logic
4. **Monitor memory** - Watch Redis memory usage in production
5. **Use key prefixes** - Organize keys by application/environment

## Troubleshooting

### Connection Refused

```python
# Check if Redis is running
import redis.asyncio as redis

try:
    client = redis.from_url("redis://localhost:6379")
    await client.ping()
    print("Connected!")
except redis.ConnectionError:
    print("Cannot connect to Redis")
```

### Timeout Errors

```python
# Increase timeouts
client = redis.from_url(
    "redis://localhost:6379",
    socket_timeout=10.0,
    socket_connect_timeout=10.0,
)
```

### Memory Issues

```python
# Check memory usage
info = await client.info("memory")
print(f"Used memory: {info['used_memory_human']}")
```
