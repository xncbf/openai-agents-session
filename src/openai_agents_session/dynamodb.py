"""DynamoDB session backend for openai-agents-python."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

from agents.memory import SessionABC

if TYPE_CHECKING:
    from agents.items import TResponseInputItem
    from types_aiobotocore_dynamodb import DynamoDBClient


class DynamoDBSession(SessionABC):
    """DynamoDB-based session storage for openai-agents.

    Stores conversation history in a DynamoDB table. Each session is stored
    as a single item with the session_id as the partition key.

    The table schema should have:
    - Partition key: `session_id` (String)

    The session data is stored in a `conversation_data` attribute as a JSON-encoded list,
    with an optional `ttl` attribute for automatic expiration.

    Args:
        session_id: Unique identifier for this session.
        dynamodb_client: An aiobotocore DynamoDB client.
        table_name: Name of the DynamoDB table.
        ttl_seconds: Time-to-live in seconds. None means no expiration.
            Requires TTL to be enabled on the table with attribute name `ttl`.

    Example:
        ```python
        from aiobotocore.session import get_session
        from openai_agents_session import DynamoDBSession

        session = get_session()
        async with session.create_client("dynamodb", region_name="us-east-1") as client:
            db_session = DynamoDBSession(
                session_id="user-123",
                dynamodb_client=client,
                table_name="agent_sessions",
                ttl_seconds=3600,
            )
        ```
    """

    def __init__(
        self,
        session_id: str,
        dynamodb_client: DynamoDBClient,
        table_name: str,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        self.session_id = session_id
        self._client = dynamodb_client
        self._table_name = table_name
        self._ttl_seconds = ttl_seconds

    def _serialize_items(self, items: list[TResponseInputItem]) -> str:
        """Serialize items to JSON string."""
        serialized = []
        for item in items:
            if hasattr(item, "model_dump"):
                serialized.append(item.model_dump(mode="json"))
            elif isinstance(item, dict):
                serialized.append(item)
            else:
                raise TypeError(f"Cannot serialize item of type {type(item)}")
        return json.dumps(serialized)

    def _deserialize_items(self, data: str) -> list[TResponseInputItem]:
        """Deserialize JSON string to items."""
        return json.loads(data)

    def _get_ttl_value(self) -> int | None:
        """Calculate TTL timestamp if configured."""
        if self._ttl_seconds is None:
            return None
        return int(time.time()) + self._ttl_seconds

    async def _get_raw_items(self) -> list[TResponseInputItem]:
        """Get raw items from DynamoDB."""
        response = await self._client.get_item(
            TableName=self._table_name,
            Key={"session_id": {"S": self.session_id}},
            ProjectionExpression="conversation_data",
        )

        if "Item" not in response:
            return []

        items_data = response["Item"].get("conversation_data", {}).get("S", "[]")
        return self._deserialize_items(items_data)

    async def _put_items(self, items: list[TResponseInputItem]) -> None:
        """Put items to DynamoDB."""
        item: dict[str, Any] = {
            "session_id": {"S": self.session_id},
            "conversation_data": {"S": self._serialize_items(items)},
            "updated_at": {"N": str(int(time.time()))},
        }

        ttl = self._get_ttl_value()
        if ttl is not None:
            item["ttl"] = {"N": str(ttl)}

        await self._client.put_item(
            TableName=self._table_name,
            Item=item,
        )

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        """Retrieve the conversation history for this session.

        Args:
            limit: Maximum number of items to retrieve. If None, returns all items.
                   When specified, returns the most recent `limit` items.

        Returns:
            List of conversation items in chronological order.
        """
        items = await self._get_raw_items()

        if limit is not None:
            return items[-limit:]
        return items

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        """Add new items to the conversation history.

        Args:
            items: List of items to add to the session.
        """
        if not items:
            return

        existing = await self._get_raw_items()
        existing.extend(items)
        await self._put_items(existing)

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item from the session.

        Returns:
            The most recent item, or None if the session is empty.
        """
        items = await self._get_raw_items()

        if not items:
            return None

        item = items.pop()
        await self._put_items(items)
        return item

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        await self._client.delete_item(
            TableName=self._table_name,
            Key={"session_id": {"S": self.session_id}},
        )

    async def close(self) -> None:
        """Close the DynamoDB client.

        Note: This is a no-op since the client is passed in.
        The caller is responsible for managing the client lifecycle.
        """
        pass


async def create_table_if_not_exists(
    client: DynamoDBClient,
    table_name: str,
    *,
    enable_ttl: bool = True,
) -> None:
    """Create the DynamoDB table if it doesn't exist.

    This is a helper function for development/testing. In production,
    you should create the table through Infrastructure as Code (Terraform, CDK, etc.).

    Args:
        client: DynamoDB client.
        table_name: Name of the table to create.
        enable_ttl: Whether to enable TTL on the table.
    """
    try:
        await client.describe_table(TableName=table_name)
        return  # Table already exists
    except client.exceptions.ResourceNotFoundException:
        pass

    await client.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "session_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Wait for table to be active
    waiter = client.get_waiter("table_exists")
    await waiter.wait(TableName=table_name)

    if enable_ttl:
        await client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                "Enabled": True,
                "AttributeName": "ttl",
            },
        )
