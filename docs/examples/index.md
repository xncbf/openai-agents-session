# Examples

This section provides practical examples for using `openai-agents-session` in various scenarios.

## Basic Examples

### Simple Redis Session

```python
import asyncio
import redis.asyncio as redis
from agents import Agent, Runner
from openai_agents_session import RedisSession


async def main():
    client = redis.from_url("redis://localhost:6379")

    session = RedisSession(
        session_id="demo-session",
        redis_client=client,
        ttl=3600,
    )

    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant.",
    )

    runner = Runner(agent=agent, session=session)

    result = await runner.run("Hello!")
    print(result.final_output)

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
```

### Simple DynamoDB Session

```python
import asyncio
from aiobotocore.session import get_session
from agents import Agent, Runner
from openai_agents_session import DynamoDBSession


async def main():
    boto_session = get_session()

    async with boto_session.create_client(
        "dynamodb",
        region_name="us-east-1",
    ) as client:
        session = DynamoDBSession(
            session_id="demo-session",
            dynamodb_client=client,
            table_name="agent_sessions",
            ttl_seconds=3600,
        )

        agent = Agent(
            name="Assistant",
            instructions="You are a helpful assistant.",
        )

        runner = Runner(agent=agent, session=session)

        result = await runner.run("Hello!")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
```

## Web Framework Integration

### FastAPI with Redis

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
import redis.asyncio as redis
from agents import Agent, Runner
from openai_agents_session import RedisSession

redis_client: redis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = redis.from_url("redis://localhost:6379")
    yield
    await redis_client.aclose()


app = FastAPI(lifespan=lifespan)
agent = Agent(name="Assistant", instructions="You are helpful.")


def get_session(user_id: str) -> RedisSession:
    return RedisSession(
        session_id=f"user-{user_id}",
        redis_client=redis_client,
        ttl=3600,
    )


@app.post("/chat/{user_id}")
async def chat(user_id: str, message: str):
    session = get_session(user_id)
    runner = Runner(agent=agent, session=session)
    result = await runner.run(message)
    return {"response": result.final_output}


@app.delete("/chat/{user_id}")
async def clear_chat(user_id: str):
    session = get_session(user_id)
    await session.clear_session()
    return {"status": "cleared"}
```

### FastAPI with DynamoDB

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiobotocore.session import get_session as get_boto_session
from agents import Agent, Runner
from openai_agents_session import DynamoDBSession

dynamodb_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global dynamodb_client
    boto_session = get_boto_session()
    async with boto_session.create_client("dynamodb") as client:
        dynamodb_client = client
        yield


app = FastAPI(lifespan=lifespan)
agent = Agent(name="Assistant", instructions="You are helpful.")


@app.post("/chat/{user_id}")
async def chat(user_id: str, message: str):
    session = DynamoDBSession(
        session_id=f"user-{user_id}",
        dynamodb_client=dynamodb_client,
        table_name="agent_sessions",
        ttl_seconds=3600,
    )
    runner = Runner(agent=agent, session=session)
    result = await runner.run(message)
    return {"response": result.final_output}
```

## Multi-Agent Scenarios

### Separate Sessions per Agent

```python
async def multi_agent_chat(user_id: str, message: str):
    # Each agent has its own session
    support_session = RedisSession(
        session_id=f"user-{user_id}-support",
        redis_client=client,
    )
    sales_session = RedisSession(
        session_id=f"user-{user_id}-sales",
        redis_client=client,
    )

    support_agent = Agent(name="Support", instructions="Handle support queries.")
    sales_agent = Agent(name="Sales", instructions="Handle sales queries.")

    # Route based on intent
    if "buy" in message.lower():
        runner = Runner(agent=sales_agent, session=sales_session)
    else:
        runner = Runner(agent=support_agent, session=support_session)

    return await runner.run(message)
```

## Session Management

### Export/Import Sessions

```python
import json

async def export_session(session: RedisSession) -> str:
    """Export session to JSON string."""
    items = await session.get_items()
    return json.dumps(items)


async def import_session(session: RedisSession, data: str) -> None:
    """Import session from JSON string."""
    items = json.loads(data)
    await session.clear_session()
    await session.add_items(items)
```

### Session Analytics

```python
async def get_session_stats(session: RedisSession) -> dict:
    """Get statistics about a session."""
    items = await session.get_items()

    user_messages = [i for i in items if i.get("role") == "user"]
    assistant_messages = [i for i in items if i.get("role") == "assistant"]

    return {
        "total_messages": len(items),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "avg_user_length": sum(len(m.get("content", "")) for m in user_messages) / len(user_messages) if user_messages else 0,
    }
```

## Next Steps

- [Integration Testing](integration-testing.md) - Test with real backends
- [API Reference](../api/index.md) - Detailed API documentation
