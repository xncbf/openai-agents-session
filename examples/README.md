# Examples

Integration tests with real Redis and DynamoDB Local services.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- uv (recommended)

## Setup

1. Start the services:

```bash
docker compose up -d
```

2. Install dependencies from the main project:

```bash
cd ..
uv sync --all-extras
```

## Running Tests

### Test Redis Session

```bash
uv run python test_redis_session.py
```

Expected output:
```
============================================================
Testing RedisSession with actual Redis
============================================================

[1] Cleared existing session data
[2] Added 4 items to session
[3] Retrieved 4 items:
    1. [user] Hello, how are you?
    2. [assistant] I'm doing well, thank you for asking!
    3. [user] What's 2 + 2?
    4. [assistant] 2 + 2 equals 4.
[4] Retrieved last 2 items:
    - [user] What's 2 + 2?
    - [assistant] 2 + 2 equals 4.
[5] Popped item: [assistant] 2 + 2 equals 4.
[6] Remaining items: 3
[7] TTL remaining: 299 seconds
[8] After clear: 0 items

============================================================
RedisSession test completed successfully!
============================================================
```

### Test DynamoDB Session

```bash
uv run python test_dynamodb_session.py
```

Expected output:
```
============================================================
Testing DynamoDBSession with actual DynamoDB Local
============================================================
Creating table 'agent_sessions'...
Table 'agent_sessions' created successfully

[1] Cleared existing session data
[2] Added 4 items to session
[3] Retrieved 4 items:
    1. [user] Hello, how are you?
    2. [assistant] I'm doing well, thank you for asking!
    3. [user] What's 2 + 2?
    4. [assistant] 2 + 2 equals 4.
[4] Retrieved last 2 items:
    - [user] What's 2 + 2?
    - [assistant] 2 + 2 equals 4.
[5] Popped item: [assistant] 2 + 2 equals 4.
[6] Remaining items: 3
[7] TTL attribute set: <timestamp>
[8] After clear: 0 items

============================================================
DynamoDBSession test completed successfully!
============================================================
```

### Test with OpenAI Agent (Optional)

Requires `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY=your-api-key
uv run python test_with_agent.py
```

## Cleanup

Stop and remove containers:

```bash
docker compose down
```
