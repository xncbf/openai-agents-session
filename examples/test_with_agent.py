"""Test session with actual OpenAI Agent (requires OPENAI_API_KEY)."""

import asyncio
import os

import redis.asyncio as redis
from agents import Agent, Runner

from openai_agents_session import RedisSession


async def main():
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("=" * 60)
        print("OPENAI_API_KEY not set - skipping agent test")
        print("Set OPENAI_API_KEY to run this test")
        print("=" * 60)
        return

    print("=" * 60)
    print("Testing RedisSession with OpenAI Agent")
    print("=" * 60)

    # Connect to Redis
    client = redis.from_url("redis://localhost:6379")

    # Create session
    session = RedisSession(
        session_id="agent-test-001",
        redis_client=client,
        ttl=3600,
    )

    # Clear previous session
    await session.clear_session()

    # Create agent
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant. Keep your responses brief.",
    )

    # Create runner with session
    runner = Runner(agent=agent, session=session)

    # First message
    print("\n[User]: Hello! My name is Alice.")
    result = await runner.run("Hello! My name is Alice.")
    print(f"[Assistant]: {result.final_output}")

    # Second message - should remember the name
    print("\n[User]: What's my name?")
    result = await runner.run("What's my name?")
    print(f"[Assistant]: {result.final_output}")

    # Check session contents
    items = await session.get_items()
    print(f"\n[Session]: {len(items)} items stored")

    # Cleanup
    await client.aclose()

    print("\n" + "=" * 60)
    print("Agent test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
