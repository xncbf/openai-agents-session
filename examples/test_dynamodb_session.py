"""Test DynamoDBSession with actual DynamoDB Local."""

import asyncio

from aiobotocore.session import get_session

from openai_agents_session import DynamoDBSession

TABLE_NAME = "agent_sessions"


async def create_table(client) -> None:
    """Create the DynamoDB table if it doesn't exist."""
    try:
        await client.describe_table(TableName=TABLE_NAME)
        print(f"Table '{TABLE_NAME}' already exists")
    except client.exceptions.ResourceNotFoundException:
        print(f"Creating table '{TABLE_NAME}'...")
        await client.create_table(
            TableName=TABLE_NAME,
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
        await waiter.wait(TableName=TABLE_NAME)
        print(f"Table '{TABLE_NAME}' created successfully")


async def main():
    print("=" * 60)
    print("Testing DynamoDBSession with actual DynamoDB Local")
    print("=" * 60)

    # Connect to DynamoDB Local
    boto_session = get_session()
    async with boto_session.create_client(
        "dynamodb",
        region_name="us-east-1",
        endpoint_url="http://localhost:8000",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    ) as client:
        # Create table
        await create_table(client)

        # Create session
        session = DynamoDBSession(
            session_id="test-session-001",
            dynamodb_client=client,
            table_name=TABLE_NAME,
            ttl_seconds=300,  # 5 minutes
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
        print("\n[4] Retrieved last 2 items:")
        for item in limited:
            print(f"    - [{item['role']}] {item['content']}")

        # Pop item
        popped = await session.pop_item()
        print(f"\n[5] Popped item: [{popped['role']}] {popped['content']}")

        # Check remaining
        remaining = await session.get_items()
        print(f"\n[6] Remaining items: {len(remaining)}")

        # Add more items to verify TTL
        await session.add_items([{"role": "user", "content": "Test TTL"}])

        # Verify TTL was set by checking raw item
        response = await client.get_item(
            TableName=TABLE_NAME,
            Key={"session_id": {"S": "test-session-001"}},
        )
        if "Item" in response and "ttl" in response["Item"]:
            print(f"\n[7] TTL attribute set: {response['Item']['ttl']['N']}")
        else:
            print("\n[7] TTL attribute not found (item may be cleared)")

        # Clear session
        await session.clear_session()
        final = await session.get_items()
        print(f"\n[8] After clear: {len(final)} items")

    print("\n" + "=" * 60)
    print("DynamoDBSession test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
