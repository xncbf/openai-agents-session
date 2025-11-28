# Agent Guidelines for openai-agents-session

This document provides guidelines for AI agents working with this codebase.

## Project Overview

`openai-agents-session` provides Redis and DynamoDB session backends for [openai-agents-python](https://github.com/openai/openai-agents-python).

### Architecture

```
src/openai_agents_session/
├── __init__.py      # Lazy imports for optional dependencies
├── redis.py         # RedisSession implementation
├── dynamodb.py      # DynamoDBSession implementation
└── py.typed         # PEP 561 marker for typed package
```

### Key Interfaces

Both `RedisSession` and `DynamoDBSession` implement the `SessionABC` interface from `openai-agents`:

```python
class SessionABC(ABC):
    session_id: str

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]: ...
    async def add_items(self, items: list[TResponseInputItem]) -> None: ...
    async def pop_item(self) -> TResponseInputItem | None: ...
    async def clear_session(self) -> None: ...
```

## Development Guidelines

### Adding New Session Backends

1. Create a new file in `src/openai_agents_session/`
2. Implement `SessionABC` from `agents.memory`
3. Add lazy import to `__init__.py`
4. Add optional dependency in `pyproject.toml`
5. Write tests using mocks (follow existing patterns in `tests/`)

### Code Style

- Use `ruff` for linting and formatting
- Use `ty` for type checking
- All async methods must be properly awaited
- Prefer explicit error messages for import failures

### Testing

- Use `fakeredis` for Redis tests
- Use `moto` for DynamoDB tests
- All tests should be async and use `pytest-asyncio`
- Mark tests with appropriate markers (`@pytest.mark.redis`, `@pytest.mark.dynamodb`)

### Common Commands

```bash
# Install dependencies
uv sync --all-extras

# Run linter
uv run ruff check .

# Run formatter
uv run ruff format .

# Run type checker
uv run ty check src/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Build package
uv build
```

## Error Handling

- Import errors should suggest the correct extra to install
- Connection errors should be propagated to the caller
- Session operations should be idempotent where possible

## Serialization

Items are serialized to JSON. Support both:
- Pydantic models with `model_dump(mode="json")`
- Plain dictionaries

## TTL Support

Both backends support TTL for automatic session expiration:
- Redis: Uses native `EXPIRE` command
- DynamoDB: Uses TTL attribute (requires table configuration)
