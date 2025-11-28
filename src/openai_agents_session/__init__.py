"""Redis and DynamoDB session backends for openai-agents-python."""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "DynamoDBSession",
    "RedisSession",
    "__version__",
]


def __getattr__(name: str):
    """Lazy import for optional dependencies."""
    if name == "RedisSession":
        try:
            from openai_agents_session.redis import RedisSession

            return RedisSession
        except ImportError as e:
            raise ImportError(
                "RedisSession requires the 'redis' extra. "
                "Install it with: pip install 'openai-agents-session[redis]'"
            ) from e

    if name == "DynamoDBSession":
        try:
            from openai_agents_session.dynamodb import DynamoDBSession

            return DynamoDBSession
        except ImportError as e:
            raise ImportError(
                "DynamoDBSession requires the 'dynamodb' extra. "
                "Install it with: pip install 'openai-agents-session[dynamodb]'"
            ) from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
