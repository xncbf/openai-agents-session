"""Redis session backend for openai-agents-python."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from agents.memory import SessionABC

if TYPE_CHECKING:
    from agents.items import TResponseInputItem
    from redis.asyncio import Redis


class RedisSession(SessionABC):
    """Redis-based session storage for openai-agents.

    Stores conversation history in Redis using a sorted set for ordered retrieval.
    Each session is stored under a key pattern: `{prefix}:{session_id}`.

    Args:
        session_id: Unique identifier for this session.
        redis_client: An async Redis client instance.
        key_prefix: Prefix for Redis keys (default: "openai_agents_session").
        ttl: Time-to-live in seconds for session data. None means no expiration.

    Example:
        ```python
        import redis.asyncio as redis
        from openai_agents_session import RedisSession

        client = redis.from_url("redis://localhost:6379")
        session = RedisSession(
            session_id="user-123",
            redis_client=client,
            ttl=3600,  # 1 hour
        )
        ```
    """

    def __init__(
        self,
        session_id: str,
        redis_client: Redis[bytes],
        *,
        key_prefix: str = "openai_agents_session",
        ttl: int | None = None,
    ) -> None:
        self.session_id = session_id
        self._client = redis_client
        self._key_prefix = key_prefix
        self._ttl = ttl

    @property
    def _key(self) -> str:
        """Redis key for this session."""
        return f"{self._key_prefix}:{self.session_id}"

    def _serialize_item(self, item: TResponseInputItem) -> str:
        """Serialize an item to JSON string."""
        if hasattr(item, "model_dump"):
            return json.dumps(cast("Any", item).model_dump(mode="json"))
        if isinstance(item, dict):
            return json.dumps(item)
        raise TypeError(f"Cannot serialize item of type {type(item)}")

    def _deserialize_item(self, data: str | bytes) -> TResponseInputItem:
        """Deserialize a JSON string to item."""
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)

    async def _refresh_ttl(self) -> None:
        """Refresh TTL if configured."""
        if self._ttl is not None:
            await self._client.expire(self._key, self._ttl)

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        """Retrieve the conversation history for this session.

        Args:
            limit: Maximum number of items to retrieve. If None, returns all items.
                   When specified, returns the most recent `limit` items.

        Returns:
            List of conversation items in chronological order.
        """
        if limit is not None:
            # Get the most recent `limit` items (negative index from the end)
            items = await self._client.lrange(self._key, -limit, -1)
        else:
            items = await self._client.lrange(self._key, 0, -1)

        await self._refresh_ttl()
        return [self._deserialize_item(item) for item in items]

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        """Add new items to the conversation history.

        Args:
            items: List of items to add to the session.
        """
        if not items:
            return

        serialized = [self._serialize_item(item) for item in items]
        await self._client.rpush(self._key, *serialized)
        await self._refresh_ttl()

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item from the session.

        Returns:
            The most recent item, or None if the session is empty.
        """
        item = await self._client.rpop(self._key)
        await self._refresh_ttl()

        if item is None:
            return None
        return self._deserialize_item(item)

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        await self._client.delete(self._key)

    async def close(self) -> None:
        """Close the Redis connection.

        Note: This only closes if the client was created internally.
        If you passed in your own client, you're responsible for closing it.
        """
        # The client is passed in, so we don't close it here
        pass
