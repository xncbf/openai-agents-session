"""Test RedisSession with actual Redis."""

import asyncio

import redis.asyncio as redis

from openai_agents_session import RedisSession


async def main():
    print("=" * 60)
    print("Testing RedisSession with actual Redis")
    print("=" * 60)

    # Connect to Redis
    client = redis.from_url("redis://localhost:6379")

    # Create session
    session = RedisSession(
        session_id="test-session-001",
        redis_client=client,
        ttl=300,  # 5 minutes
    )

    # Clear any existing data
    await session.clear_session()
    print("\n[1] Cleared existing session data")

    # Add items
    items = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
        {"role": "user", "content": "What's 2 + 2?"},
        {"role": "assistant", "content": "2 + 2 equals 4."},
    ]

    await session.add_items(items)
    print(f"\n[2] Added {len(items)} items to session")

    # Get all items
    retrieved = await session.get_items()
    print(f"\n[3] Retrieved {len(retrieved)} items:")
    for i, item in enumerate(retrieved, 1):
        print(f"    {i}. [{item['role']}] {item['content']}")

    # Get with limit
    limited = await session.get_items(limit=2)
    print(f"\n[4] Retrieved last 2 items:")
    for item in limited:
        print(f"    - [{item['role']}] {item['content']}")

    # Pop item
    popped = await session.pop_item()
    print(f"\n[5] Popped item: [{popped['role']}] {popped['content']}")

    # Check remaining
    remaining = await session.get_items()
    print(f"\n[6] Remaining items: {len(remaining)}")

    # Check TTL
    ttl = await client.ttl(session._key)
    print(f"\n[7] TTL remaining: {ttl} seconds")

    # Clear session
    await session.clear_session()
    final = await session.get_items()
    print(f"\n[8] After clear: {len(final)} items")

    # Close connection
    await client.aclose()

    print("\n" + "=" * 60)
    print("RedisSession test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
