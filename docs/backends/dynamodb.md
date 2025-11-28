# DynamoDB Backend

The DynamoDB backend provides serverless, scalable session storage with automatic expiration using AWS DynamoDB.

## Overview

DynamoDB is ideal for:

- **Serverless architectures** - No servers to manage
- **Auto-scaling** - Handles any workload automatically
- **Global distribution** - Multi-region replication available
- **Durability** - Data is replicated across multiple AZs

## Installation

```bash
pip install "openai-agents-session[dynamodb]"
```

## Basic Usage

```python
from aiobotocore.session import get_session
from openai_agents_session import DynamoDBSession

async def main():
    boto_session = get_session()
    async with boto_session.create_client(
        "dynamodb",
        region_name="us-east-1",
    ) as client:
        session = DynamoDBSession(
            session_id="user-123",
            dynamodb_client=client,
            table_name="agent_sessions",
            ttl_seconds=3600,
        )
        # Use session...
```

## Configuration Options

### DynamoDBSession Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | `str` | Required | Unique identifier for the session |
| `dynamodb_client` | `DynamoDBClient` | Required | aiobotocore DynamoDB client |
| `table_name` | `str` | Required | DynamoDB table name |
| `ttl_seconds` | `int \| None` | `None` | Time-to-live in seconds |

## Table Schema

### Required Schema

Create a table with the following schema:

| Attribute | Type | Key |
|-----------|------|-----|
| `session_id` | String (S) | Partition Key (HASH) |

### Terraform

```hcl
resource "aws_dynamodb_table" "agent_sessions" {
  name         = "agent_sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Environment = "production"
    Application = "openai-agents"
  }
}
```

### AWS CDK

```python
from aws_cdk import aws_dynamodb as dynamodb

table = dynamodb.Table(
    self,
    "AgentSessions",
    table_name="agent_sessions",
    partition_key=dynamodb.Attribute(
        name="session_id",
        type=dynamodb.AttributeType.STRING,
    ),
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    time_to_live_attribute="ttl",
)
```

### AWS CLI

```bash
aws dynamodb create-table \
    --table-name agent_sessions \
    --key-schema AttributeName=session_id,KeyType=HASH \
    --attribute-definitions AttributeName=session_id,AttributeType=S \
    --billing-mode PAY_PER_REQUEST

# Enable TTL
aws dynamodb update-time-to-live \
    --table-name agent_sessions \
    --time-to-live-specification "Enabled=true,AttributeName=ttl"
```

### Helper Function

For development, you can use the built-in helper:

```python
from openai_agents_session.dynamodb import create_table_if_not_exists

await create_table_if_not_exists(
    client=dynamodb_client,
    table_name="agent_sessions",
    enable_ttl=True,
)
```

!!! warning "Production Use"
    Don't use `create_table_if_not_exists` in production. Use Infrastructure as Code (Terraform, CDK, CloudFormation) instead.

## IAM Permissions

### Minimum Required Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/agent_sessions"
        }
    ]
}
```

### For Development (with table creation)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:DeleteItem",
                "dynamodb:CreateTable",
                "dynamodb:DescribeTable",
                "dynamodb:UpdateTimeToLive"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/agent_sessions"
        }
    ]
}
```

## Data Storage Format

Each session is stored as a single DynamoDB item:

```json
{
    "session_id": {"S": "user-123"},
    "conversation_data": {"S": "[{\"role\":\"user\",\"content\":\"Hello\"}]"},
    "updated_at": {"N": "1699900000"},
    "ttl": {"N": "1699903600"}
}
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `session_id` | String | Partition key |
| `conversation_data` | String | JSON-encoded message list |
| `updated_at` | Number | Unix timestamp of last update |
| `ttl` | Number | Unix timestamp for expiration |

## Operations

### Get Items

```python
# Get all items
items = await session.get_items()

# Get last 10 items
recent = await session.get_items(limit=10)
```

### Add Items

```python
await session.add_items([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
])
```

### Pop Item

```python
last = await session.pop_item()
```

### Clear Session

```python
await session.clear_session()
```

## Local Development

### DynamoDB Local with Docker

```bash
docker run -d -p 8000:8000 amazon/dynamodb-local
```

### Connect to Local DynamoDB

```python
boto_session = get_session()
async with boto_session.create_client(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url="http://localhost:8000",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
) as client:
    session = DynamoDBSession(
        session_id="test-session",
        dynamodb_client=client,
        table_name="agent_sessions",
    )
```

## Production Deployment

### AWS Lambda

```python
import os
from aiobotocore.session import get_session
from openai_agents_session import DynamoDBSession

# Create client outside handler for connection reuse
boto_session = get_session()

async def handler(event, context):
    async with boto_session.create_client("dynamodb") as client:
        session = DynamoDBSession(
            session_id=event["user_id"],
            dynamodb_client=client,
            table_name=os.environ["TABLE_NAME"],
            ttl_seconds=3600,
        )
        # Process request...
```

### ECS/Fargate

```python
from aiobotocore.session import get_session

# Use IAM role attached to task
boto_session = get_session()

async with boto_session.create_client(
    "dynamodb",
    region_name="us-east-1",
) as client:
    session = DynamoDBSession(...)
```

## Cost Optimization

### On-Demand vs Provisioned

| Mode | Best For |
|------|----------|
| On-Demand | Variable workloads, new applications |
| Provisioned | Predictable, steady workloads |

### Capacity Estimation

Each operation consumes:

- **GetItem**: 0.5 RCU (eventually consistent) or 1 RCU (strongly consistent)
- **PutItem**: 1 WCU per KB
- **DeleteItem**: 1 WCU per KB

### Reserved Capacity

For steady workloads, consider reserved capacity for up to 77% savings.

## Monitoring

### CloudWatch Metrics

Monitor these metrics:

- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `ThrottledRequests`
- `SystemErrors`

### CloudWatch Alarms

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name "DynamoDB-Throttling" \
    --metric-name ThrottledRequests \
    --namespace AWS/DynamoDB \
    --statistic Sum \
    --period 60 \
    --threshold 1 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=TableName,Value=agent_sessions
```

## Best Practices

1. **Use TTL** - Always set TTL to prevent unbounded growth
2. **Right-size items** - Keep items under 400KB (DynamoDB limit)
3. **Use on-demand billing** - For variable or unpredictable workloads
4. **Enable point-in-time recovery** - For production tables
5. **Use VPC endpoints** - For better security and lower latency

## Troubleshooting

### ValidationException: Reserved Keyword

If you see errors about reserved keywords, ensure you're using the latest version which uses `conversation_data` instead of `items`.

### Provisioned Throughput Exceeded

```python
# Use exponential backoff
import asyncio
from botocore.exceptions import ClientError

async def safe_operation():
    for attempt in range(5):
        try:
            await session.add_items(items)
            break
        except ClientError as e:
            if e.response["Error"]["Code"] == "ProvisionedThroughputExceededException":
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

### Item Too Large

DynamoDB items are limited to 400KB. For large conversation histories, consider:

1. Limiting history length with `get_items(limit=N)`
2. Using S3 for overflow storage
3. Summarizing old conversations
