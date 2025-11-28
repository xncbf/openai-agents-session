# openai-agents-session

**Redis and DynamoDB session backends for [openai-agents-python](https://github.com/openai/openai-agents-python)**

[![PyPI version](https://badge.fury.io/py/openai-agents-session.svg)](https://badge.fury.io/py/openai-agents-session)
[![Python Versions](https://img.shields.io/pypi/pyversions/openai-agents-session.svg)](https://pypi.org/project/openai-agents-session/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

`openai-agents-session` provides production-ready session storage backends for the OpenAI Agents Python SDK. It enables persistent conversation history across multiple interactions with your AI agents.

### Features

- **Redis Backend**: High-performance in-memory storage with optional TTL
- **DynamoDB Backend**: Serverless, scalable cloud storage with automatic expiration
- **Async Native**: Built with `asyncio` for non-blocking operations
- **Type Safe**: Full type hints and PEP 561 compliant
- **Zero Config**: Works out of the box with sensible defaults

## Quick Example

```python
import redis.asyncio as redis
from agents import Agent, Runner
from openai_agents_session import RedisSession

# Create Redis client
client = redis.from_url("redis://localhost:6379")

# Create session with 1-hour TTL
session = RedisSession(
    session_id="user-123",
    redis_client=client,
    ttl=3600,
)

# Use with OpenAI Agent
agent = Agent(name="Assistant", instructions="You are a helpful assistant.")
runner = Runner(agent=agent, session=session)

# Conversation persists across calls
result = await runner.run("Hello! My name is Alice.")
result = await runner.run("What's my name?")  # Agent remembers "Alice"
```

## Installation

=== "Redis only"

    ```bash
    pip install "openai-agents-session[redis]"
    ```

=== "DynamoDB only"

    ```bash
    pip install "openai-agents-session[dynamodb]"
    ```

=== "All backends"

    ```bash
    pip install "openai-agents-session[all]"
    ```

## Why Use This?

The default `openai-agents-python` stores conversation history in memory, which means:

- History is lost when your application restarts
- Each instance has its own isolated memory
- No way to resume conversations across sessions

With `openai-agents-session`, you get:

- **Persistent storage** that survives restarts
- **Shared state** across multiple application instances
- **Automatic expiration** with configurable TTL
- **Scalable backends** for production workloads

## Next Steps

- [Installation Guide](getting-started/installation.md) - Detailed setup instructions
- [Quick Start](getting-started/quickstart.md) - Get up and running in minutes
- [Redis Backend](backends/redis.md) - Redis-specific configuration
- [DynamoDB Backend](backends/dynamodb.md) - DynamoDB setup and usage
