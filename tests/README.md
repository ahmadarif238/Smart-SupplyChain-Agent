# Tests Directory

This directory contains all test files for the Smart Supply Chain Agent.

## Test Files

### Unit Tests

- **`test_auth.py`** - Authentication and JWT token tests
- **`test_decision.py`** - Decision node logic tests
- **`test_imports.py`** - Import validation tests
- **`test_nodes.py`** - Individual node unit tests
- **`test_parser.py`** - Data parsing tests

### Integration Tests

- **`test_negotiation_flow.py`** - End-to-end negotiation workflow tests
- **`test_job_status.py`** - Job execution and status tests
- **`test_langgraph_phase1.py`** - LangGraph workflow Phase 1 tests

### API Tests

- **`test_api_phase1.py`** - API endpoint Phase 1 tests

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test File

```bash
pytest tests/test_negotiation_flow.py -v
```

### With Coverage

```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

This will generate:
- Terminal coverage report
- HTML coverage report in `htmlcov/` directory

### Test Categories

Run specific categories using markers:

```bash
# Unit tests only
pytest tests/ -m unit

# Integration tests only
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"
```

## Test Database

Tests use a separate test database. Set in environment:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/supply_chain_test
```

## Writing New Tests

Follow these guidelines:

1. **File naming**: `test_*.py`
2. **Function naming**: `test_<functionality>`
3. **Use fixtures**: Define in `conftest.py`
4. **Async tests**: Use `@pytest.mark.asyncio`
5. **Markers**: Add appropriate pytest markers

Example:

```python
import pytest
from app.agents.nodes.forecast_node import ForecastNode

@pytest.mark.asyncio
async def test_forecast_generation():
    """Test that forecast node generates predictions."""
    node = ForecastNode()
    result = await node.forecast(...)
    assert result is not None
    assert len(result.forecast) == 7  # 7-day forecast
```

## Continuous Integration

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

See `.github/workflows/ci.yml` for CI configuration.

## Test Coverage Goals

Aim for:
- **>70%** overall coverage
- **>80%** for critical business logic (agents, decision nodes)
- **>50%** for routes and utilities
