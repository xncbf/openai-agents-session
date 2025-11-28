# Claude Code Instructions

This file provides instructions for Claude Code when working with this repository.

## Quick Reference

Read `AGENTS.md` for detailed development guidelines, architecture, and coding patterns.

## Project Context

- **Purpose**: Redis and DynamoDB session backends for openai-agents-python
- **Language**: Python 3.10+
- **Package Manager**: uv
- **Linter/Formatter**: ruff
- **Type Checker**: ty

## Key Files

| File | Purpose |
|------|---------|
| `src/openai_agents_session/redis.py` | Redis session implementation |
| `src/openai_agents_session/dynamodb.py` | DynamoDB session implementation |
| `tests/test_redis.py` | Redis tests with fakeredis |
| `tests/test_dynamodb.py` | DynamoDB tests with moto |

## Common Tasks

### Before Making Changes
```bash
uv sync --all-extras  # Install all dependencies
```

### After Making Changes
```bash
uv run ruff check .   # Lint
uv run ruff format .  # Format
uv run ty check src/  # Type check
uv run pytest         # Test
```

### Adding a New Backend

1. Create `src/openai_agents_session/<backend>.py`
2. Implement `SessionABC` interface
3. Add lazy import in `__init__.py`
4. Add dependency in `pyproject.toml` under `[project.optional-dependencies]`
5. Create test file in `tests/test_<backend>.py`
6. Update `README.md` with usage example

## Testing Notes

- Use mocks, not real services
- Redis: `fakeredis` library
- DynamoDB: `moto` library with `@mock_aws` decorator
- All tests must be async

## Dependencies

Core dependency: `openai-agents>=0.1.0`

Optional:
- `redis`: Redis async client
- `dynamodb`: aiobotocore with DynamoDB support

## Important Patterns

### Lazy Imports
The `__init__.py` uses `__getattr__` for lazy loading to avoid importing optional dependencies unless needed.

### Error Messages
Always suggest the correct install command:
```python
raise ImportError(
    "RedisSession requires the 'redis' extra. "
    "Install it with: pip install 'openai-agents-session[redis]'"
) from e
```
