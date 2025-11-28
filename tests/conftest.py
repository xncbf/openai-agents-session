"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_items() -> list[dict]:
    """Sample conversation items for testing."""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "I don't have access to weather data."},
    ]


@pytest.fixture
def session_id() -> str:
    """Generate a unique session ID for testing."""
    import uuid

    return f"test-session-{uuid.uuid4().hex[:8]}"
