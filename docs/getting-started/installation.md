# Installation

## Requirements

- Python 3.10 or higher
- An OpenAI API key (for using with agents)

## Installing with pip

### Redis Backend

If you only need Redis support:

```bash
pip install "openai-agents-session[redis]"
```

This installs:

- `openai-agents-session`
- `openai-agents`
- `redis` (async Redis client)

### DynamoDB Backend

If you only need DynamoDB support:

```bash
pip install "openai-agents-session[dynamodb]"
```

This installs:

- `openai-agents-session`
- `openai-agents`
- `aiobotocore` (async AWS SDK)
- `types-aiobotocore[dynamodb]` (type stubs)

### All Backends

To install all available backends:

```bash
pip install "openai-agents-session[all]"
```

## Installing with uv

[uv](https://github.com/astral-sh/uv) is a fast Python package manager:

```bash
# Redis only
uv add "openai-agents-session[redis]"

# DynamoDB only
uv add "openai-agents-session[dynamodb]"

# All backends
uv add "openai-agents-session[all]"
```

## Installing with Poetry

```bash
# Redis only
poetry add "openai-agents-session[redis]"

# DynamoDB only
poetry add "openai-agents-session[dynamodb]"

# All backends
poetry add "openai-agents-session[all]"
```

## Development Installation

To contribute to the project:

```bash
git clone https://github.com/xncbf/openai-agents-session.git
cd openai-agents-session

# Using uv (recommended)
uv sync --all-extras

# Or using pip
pip install -e ".[dev]"
```

## Verifying Installation

```python
# Check Redis backend
from openai_agents_session import RedisSession
print("Redis backend available!")

# Check DynamoDB backend
from openai_agents_session import DynamoDBSession
print("DynamoDB backend available!")
```

## Backend Requirements

### Redis

You need a running Redis server:

=== "Docker"

    ```bash
    docker run -d -p 6379:6379 redis:7-alpine
    ```

=== "Local Installation"

    ```bash
    # macOS
    brew install redis
    brew services start redis

    # Ubuntu/Debian
    sudo apt-get install redis-server
    sudo systemctl start redis
    ```

### DynamoDB

You can use either DynamoDB Local for development or AWS DynamoDB for production:

=== "DynamoDB Local (Docker)"

    ```bash
    docker run -d -p 8000:8000 amazon/dynamodb-local
    ```

=== "AWS DynamoDB"

    Configure AWS credentials:

    ```bash
    aws configure
    # Or set environment variables:
    export AWS_ACCESS_KEY_ID=your-access-key
    export AWS_SECRET_ACCESS_KEY=your-secret-key
    export AWS_DEFAULT_REGION=us-east-1
    ```

## Next Steps

- [Quick Start Guide](quickstart.md) - Build your first persistent agent
- [Redis Backend](../backends/redis.md) - Redis configuration options
- [DynamoDB Backend](../backends/dynamodb.md) - DynamoDB setup and IAM
