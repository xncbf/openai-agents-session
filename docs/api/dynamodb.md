# DynamoDBSession

DynamoDB-based session storage for openai-agents.

## Class Definition

::: openai_agents_session.dynamodb.DynamoDBSession
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get_items
        - add_items
        - pop_item
        - clear_session

## Usage Example

```python
from aiobotocore.session import get_session
from openai_agents_session import DynamoDBSession

# Create client
boto_session = get_session()
async with boto_session.create_client(
    "dynamodb",
    region_name="us-east-1",
) as client:
    # Create session
    session = DynamoDBSession(
        session_id="user-123",
        dynamodb_client=client,
        table_name="agent_sessions",
        ttl_seconds=3600,
    )

    # Add items
    await session.add_items([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ])

    # Get items
    items = await session.get_items()

    # Clear session
    await session.clear_session()
```

## Parameters

### session_id

- **Type**: `str`
- **Required**: Yes

Unique identifier for the session. Used as the partition key in DynamoDB.

### dynamodb_client

- **Type**: `DynamoDBClient`
- **Required**: Yes

An aiobotocore DynamoDB client instance.

### table_name

- **Type**: `str`
- **Required**: Yes

Name of the DynamoDB table to use.

### ttl_seconds

- **Type**: `int | None`
- **Default**: `None`

Time-to-live in seconds. If set, items will be automatically deleted after this duration. Requires TTL to be enabled on the table with attribute name `ttl`.

## Methods

### get_items

```python
async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]
```

Retrieve conversation history.

**Parameters:**

- `limit`: Maximum number of items to return. Returns the most recent items.

**Returns:** List of conversation items in chronological order.

### add_items

```python
async def add_items(self, items: list[TResponseInputItem]) -> None
```

Add new items to the conversation history.

**Parameters:**

- `items`: List of items to add.

### pop_item

```python
async def pop_item(self) -> TResponseInputItem | None
```

Remove and return the most recent item.

**Returns:** The removed item, or `None` if the session is empty.

### clear_session

```python
async def clear_session(self) -> None
```

Delete the entire session from DynamoDB.

## Helper Functions

### create_table_if_not_exists

::: openai_agents_session.dynamodb.create_table_if_not_exists
    options:
      show_root_heading: true
      show_source: true

## DynamoDB Item Structure

Each session is stored as a single item:

| Attribute | Type | Description |
|-----------|------|-------------|
| `session_id` | String (S) | Partition key |
| `conversation_data` | String (S) | JSON-encoded list of items |
| `updated_at` | Number (N) | Unix timestamp |
| `ttl` | Number (N) | TTL timestamp (optional) |

## See Also

- [DynamoDB Backend Guide](../backends/dynamodb.md)
- [Quick Start](../getting-started/quickstart.md)
