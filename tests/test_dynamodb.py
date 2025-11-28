"""Tests for DynamoDBSession."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from openai_agents_session.dynamodb import DynamoDBSession


@pytest.fixture
def mock_dynamodb_client():
    """Create a mock DynamoDB client for testing."""
    client = MagicMock()
    client.get_item = AsyncMock()
    client.put_item = AsyncMock()
    client.delete_item = AsyncMock()
    return client


@pytest.fixture
def dynamodb_session(mock_dynamodb_client, session_id: str) -> DynamoDBSession:
    """Create a DynamoDBSession for testing."""
    return DynamoDBSession(
        session_id=session_id,
        dynamodb_client=mock_dynamodb_client,
        table_name="test_table",
    )


class InMemoryDynamoDBClient:
    """In-memory DynamoDB client for testing."""

    def __init__(self):
        self._tables: dict[str, dict[str, Any]] = {}

    async def get_item(self, TableName: str, Key: dict, **kwargs) -> dict:
        table = self._tables.get(TableName, {})
        session_id = Key["session_id"]["S"]
        if session_id in table:
            # Filter to only return requested projection
            projection = kwargs.get("ProjectionExpression", "")
            if projection:
                filtered_item = {"session_id": table[session_id]["session_id"]}
                for attr in projection.split(","):
                    attr = attr.strip()
                    if attr in table[session_id]:
                        filtered_item[attr] = table[session_id][attr]
                return {"Item": filtered_item}
            return {"Item": table[session_id]}
        return {}

    async def put_item(self, TableName: str, Item: dict, **kwargs) -> dict:
        if TableName not in self._tables:
            self._tables[TableName] = {}
        session_id = Item["session_id"]["S"]
        self._tables[TableName][session_id] = Item
        return {}

    async def delete_item(self, TableName: str, Key: dict, **kwargs) -> dict:
        table = self._tables.get(TableName, {})
        session_id = Key["session_id"]["S"]
        if session_id in table:
            del table[session_id]
        return {}


@pytest.fixture
def inmemory_dynamodb_client():
    """Create an in-memory DynamoDB client for testing."""
    return InMemoryDynamoDBClient()


@pytest.fixture
def inmemory_dynamodb_session(inmemory_dynamodb_client, session_id: str) -> DynamoDBSession:
    """Create a DynamoDBSession with in-memory client for testing."""
    return DynamoDBSession(
        session_id=session_id,
        dynamodb_client=inmemory_dynamodb_client,  # type: ignore[arg-type]
        table_name="test_table",
    )


@pytest.mark.dynamodb
class TestDynamoDBSession:
    """Test suite for DynamoDBSession."""

    async def test_add_and_get_items(
        self, inmemory_dynamodb_session: DynamoDBSession, sample_items: list[dict]
    ):
        """Test adding and retrieving items."""
        await inmemory_dynamodb_session.add_items(sample_items)
        retrieved = await inmemory_dynamodb_session.get_items()

        assert len(retrieved) == len(sample_items)
        for original, retrieved_item in zip(sample_items, retrieved, strict=True):
            assert retrieved_item["role"] == original["role"]
            assert retrieved_item["content"] == original["content"]

    async def test_get_items_with_limit(
        self, inmemory_dynamodb_session: DynamoDBSession, sample_items: list[dict]
    ):
        """Test retrieving items with a limit."""
        await inmemory_dynamodb_session.add_items(sample_items)

        # Get only the last 2 items
        retrieved = await inmemory_dynamodb_session.get_items(limit=2)

        assert len(retrieved) == 2
        assert retrieved[0]["content"] == "What's the weather like?"
        assert retrieved[1]["content"] == "I don't have access to weather data."

    async def test_pop_item(
        self, inmemory_dynamodb_session: DynamoDBSession, sample_items: list[dict]
    ):
        """Test popping the most recent item."""
        await inmemory_dynamodb_session.add_items(sample_items)

        popped = await inmemory_dynamodb_session.pop_item()
        assert popped is not None
        assert popped["content"] == "I don't have access to weather data."

        remaining = await inmemory_dynamodb_session.get_items()
        assert len(remaining) == 3

    async def test_pop_item_empty_session(self, inmemory_dynamodb_session: DynamoDBSession):
        """Test popping from an empty session."""
        popped = await inmemory_dynamodb_session.pop_item()
        assert popped is None

    async def test_clear_session(
        self, inmemory_dynamodb_session: DynamoDBSession, sample_items: list[dict]
    ):
        """Test clearing all items."""
        await inmemory_dynamodb_session.add_items(sample_items)
        await inmemory_dynamodb_session.clear_session()

        retrieved = await inmemory_dynamodb_session.get_items()
        assert len(retrieved) == 0

    async def test_add_empty_items(self, inmemory_dynamodb_session: DynamoDBSession):
        """Test adding an empty list of items."""
        await inmemory_dynamodb_session.add_items([])
        retrieved = await inmemory_dynamodb_session.get_items()
        assert len(retrieved) == 0

    async def test_session_isolation(
        self, inmemory_dynamodb_client, sample_items: list[dict]
    ):
        """Test that different sessions are isolated."""
        session1 = DynamoDBSession(
            session_id="session-1",
            dynamodb_client=inmemory_dynamodb_client,  # type: ignore[arg-type]
            table_name="test_table",
        )
        session2 = DynamoDBSession(
            session_id="session-2",
            dynamodb_client=inmemory_dynamodb_client,  # type: ignore[arg-type]
            table_name="test_table",
        )

        await session1.add_items(sample_items[:2])
        await session2.add_items(sample_items[2:])

        items1 = await session1.get_items()
        items2 = await session2.get_items()

        assert len(items1) == 2
        assert len(items2) == 2
        assert items1[0]["content"] != items2[0]["content"]

    async def test_ttl_setting(
        self, inmemory_dynamodb_client, session_id: str, sample_items: list[dict]
    ):
        """Test TTL is set in the item."""
        session = DynamoDBSession(
            session_id=session_id,
            dynamodb_client=inmemory_dynamodb_client,  # type: ignore[arg-type]
            table_name="test_table",
            ttl_seconds=3600,
        )

        await session.add_items(sample_items)

        # Get the raw item to check TTL
        response = await inmemory_dynamodb_client.get_item(
            TableName="test_table",
            Key={"session_id": {"S": session_id}},
        )

        assert "Item" in response
        assert "ttl" in response["Item"]
        assert "N" in response["Item"]["ttl"]


@pytest.mark.dynamodb
class TestDynamoDBSessionWithMock:
    """Test suite using mock client to verify API calls."""

    async def test_get_items_calls_dynamodb(
        self, mock_dynamodb_client, session_id: str
    ):
        """Test that get_items makes correct DynamoDB API call."""
        mock_dynamodb_client.get_item.return_value = {}

        session = DynamoDBSession(
            session_id=session_id,
            dynamodb_client=mock_dynamodb_client,
            table_name="test_table",
        )

        await session.get_items()

        mock_dynamodb_client.get_item.assert_called_once()
        call_kwargs = mock_dynamodb_client.get_item.call_args.kwargs
        assert call_kwargs["TableName"] == "test_table"
        assert call_kwargs["Key"]["session_id"]["S"] == session_id

    async def test_clear_session_calls_delete_item(
        self, mock_dynamodb_client, session_id: str
    ):
        """Test that clear_session makes correct DynamoDB API call."""
        session = DynamoDBSession(
            session_id=session_id,
            dynamodb_client=mock_dynamodb_client,
            table_name="test_table",
        )

        await session.clear_session()

        mock_dynamodb_client.delete_item.assert_called_once()
        call_kwargs = mock_dynamodb_client.delete_item.call_args.kwargs
        assert call_kwargs["TableName"] == "test_table"
        assert call_kwargs["Key"]["session_id"]["S"] == session_id
