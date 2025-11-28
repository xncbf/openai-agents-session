"""Tests for RedisSession."""

from __future__ import annotations

import pytest
from fakeredis import aioredis

from openai_agents_session.redis import RedisSession


@pytest.fixture
async def redis_client():
    """Create a fake Redis client for testing."""
    client = aioredis.FakeRedis()
    yield client
    await client.aclose()


@pytest.fixture
async def redis_session(redis_client, session_id: str) -> RedisSession:
    """Create a RedisSession for testing."""
    return RedisSession(
        session_id=session_id,
        redis_client=redis_client,
    )


@pytest.mark.redis
class TestRedisSession:
    """Test suite for RedisSession."""

    async def test_add_and_get_items(self, redis_session: RedisSession, sample_items: list[dict]):
        """Test adding and retrieving items."""
        await redis_session.add_items(sample_items)
        retrieved = await redis_session.get_items()

        assert len(retrieved) == len(sample_items)
        for original, retrieved_item in zip(sample_items, retrieved, strict=True):
            assert retrieved_item["role"] == original["role"]
            assert retrieved_item["content"] == original["content"]

    async def test_get_items_with_limit(
        self, redis_session: RedisSession, sample_items: list[dict]
    ):
        """Test retrieving items with a limit."""
        await redis_session.add_items(sample_items)

        # Get only the last 2 items
        retrieved = await redis_session.get_items(limit=2)

        assert len(retrieved) == 2
        assert retrieved[0]["content"] == "What's the weather like?"
        assert retrieved[1]["content"] == "I don't have access to weather data."

    async def test_pop_item(self, redis_session: RedisSession, sample_items: list[dict]):
        """Test popping the most recent item."""
        await redis_session.add_items(sample_items)

        popped = await redis_session.pop_item()
        assert popped is not None
        assert popped["content"] == "I don't have access to weather data."

        remaining = await redis_session.get_items()
        assert len(remaining) == 3

    async def test_pop_item_empty_session(self, redis_session: RedisSession):
        """Test popping from an empty session."""
        popped = await redis_session.pop_item()
        assert popped is None

    async def test_clear_session(self, redis_session: RedisSession, sample_items: list[dict]):
        """Test clearing all items."""
        await redis_session.add_items(sample_items)
        await redis_session.clear_session()

        retrieved = await redis_session.get_items()
        assert len(retrieved) == 0

    async def test_add_empty_items(self, redis_session: RedisSession):
        """Test adding an empty list of items."""
        await redis_session.add_items([])
        retrieved = await redis_session.get_items()
        assert len(retrieved) == 0

    async def test_session_isolation(self, redis_client, sample_items: list[dict]):
        """Test that different sessions are isolated."""
        session1 = RedisSession(session_id="session-1", redis_client=redis_client)
        session2 = RedisSession(session_id="session-2", redis_client=redis_client)

        await session1.add_items(sample_items[:2])
        await session2.add_items(sample_items[2:])

        items1 = await session1.get_items()
        items2 = await session2.get_items()

        assert len(items1) == 2
        assert len(items2) == 2
        assert items1[0]["content"] != items2[0]["content"]

    async def test_key_prefix(self, redis_client, session_id: str):
        """Test custom key prefix."""
        session = RedisSession(
            session_id=session_id,
            redis_client=redis_client,
            key_prefix="custom_prefix",
        )

        assert session._key == f"custom_prefix:{session_id}"

    async def test_ttl_setting(self, redis_client, session_id: str, sample_items: list[dict]):
        """Test TTL is set correctly."""
        session = RedisSession(
            session_id=session_id,
            redis_client=redis_client,
            ttl=3600,
        )

        await session.add_items(sample_items)

        # Check that TTL was set
        ttl = await redis_client.ttl(session._key)
        assert ttl > 0
        assert ttl <= 3600
