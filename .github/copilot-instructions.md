# Smart Supply Chain AI Agent — Copilot Instructions

## Architecture Overview

This is an autonomous supply chain management system that continuously monitors inventory, predicts demand, and makes procurement decisions using LLM-powered reasoning.

**Core Data Flow:**
1. **Fetch Data Node** (`app/agents/nodes/fetch_data_node.py`) — Retrieves inventory, recent sales, orders, and alerts from PostgreSQL
2. **Forecast Node** (`app/agents/nodes/forecast_node.py`) — Uses Groq LLM (qwen/qwen3-32b) to predict 7-day sales per SKU; falls back to baseline average if LLM fails
3. **Decision Node** (`app/agents/nodes/decision_node.py`) — Applies business logic to determine if reordering is needed
4. **Action Node** (`app/agents/nodes/action_node.py`) — Executes decisions (creates orders, sends alerts)
5. **Memory Node** (`app/agents/nodes/memory_node.py`) — Persists cycle context, decisions, and results to `agent_memory` table

**Controller:** `AgentController` in `app/agents/langgraph_flow.py` orchestrates this cycle, runs continuously in background thread.

## Service Architecture

- **Backend API**: FastAPI (`main.py`) exposes REST endpoints on :8000
- **Routes** (`app/routes/`): Modular routers for inventory, sales, orders, alerts, agent, feedback, memory
- **Frontend UI**: Streamlit dashboard (`streamlit_app.py`) queries FastAPI backend
- **Database**: PostgreSQL via SQLAlchemy; models in `app/models/schemas.py`
- **LLM Integration**: Groq API via `app/utils/groq_utils.py` with graceful fallbacks

## Key Patterns & Conventions

### LLM Response Handling
- **Always handle LLM failures gracefully.** Groq API calls may timeout or return invalid JSON.
- Use `try_parse_json_from_text()` to extract JSON from LLM responses; it removes `<think>` blocks and parsing artifacts.
- Implement sensible **baseline fallbacks** — e.g., `forecast_node` falls back to rolling average if parsing fails.
- Prompt templates are centralized in `app/agents/reasoning_prompts.py`; format with context-specific data like `{sku_summary}`, `{recent_sales}`.

### Database Operations
- All DB interactions use `SessionLocal()` session factory from `app/models/database.py`.
- Routes depend on `get_db()` helper that yields a session and closes it.
- Serialize models to dicts using `serialize_model()` from `app/utils/common.py` — removes SQLAlchemy internal state.
- Agent cycle saves complete decision context to `AgentMemory` table for audit/replay; see `MemoryManager.save_memory()`.

### Background Agent Loop
- Agent runs in daemon thread started at FastAPI startup (`app/routes/agent.py:start_background_agent()`).
- Cycle interval varies: FAST_INTERVAL (10 min) if urgent actions pending, otherwise NORMAL_INTERVAL (1 hour).
- Each cycle logs results and stores summary in `agent_run_summaries` table.
- **Do not block the main thread.** Async I/O is not used; threading isolates the autonomous loop.

### Request/Response Serialization
- Streamlit dashboard uses helper functions `api_get()` and `api_post()` with retry/error handling.
- JSON endpoints should return nested objects; extract relevant fields in frontend.
- Timeout is 30s by default; adjust in `DEFAULT_TIMEOUT` if calling slow endpoints.

## Development Workflows

### Running Locally
```bash
# Activate virtual environment
.\myenv\Scripts\Activate.ps1

# Start FastAPI backend (uvicorn auto-reload on code changes)
uvicorn main:app --reload --port 8000

# In another terminal, start Streamlit frontend
streamlit run streamlit_app.py

# Agent runs autonomously in background; monitor logs or call GET /agent/run_once for single cycle
```

### Adding New Inventory Routes
1. Create route file in `app/routes/` (e.g., `new_feature.py`)
2. Define router with prefix: `router = APIRouter(prefix="/feature", tags=["Feature"])`
3. Add `Depends(get_db)` for DB access
4. Include router in `main.py`: `app.include_router(new_router)`
5. Serialize SQLAlchemy models before returning: use `serialize_model()`

### Adding LLM-Powered Logic
1. Add prompt template to `app/agents/reasoning_prompts.py` with template vars like `{sku}`, `{forecast}`
2. Call `query_groq("model_name", prompt_text)` from `app/utils/groq_utils.py`
3. **Always wrap in try/except** and parse JSON with `try_parse_json_from_text()`
4. Provide fallback behavior (baseline stats, default values, or error flags)

### Environment Configuration
- `.env` file required with:
  - `DATABASE_URL` (PostgreSQL): `postgresql://user:password@localhost/supply_chain_db`
  - `GROQ_API_KEY` (Groq): API key from Groq console
  - `API_BASE` (optional, Streamlit): defaults to `http://127.0.0.1:8000`
  - `TELEGRAM_BOT_TOKEN` (optional): if using Telegram alerts

## Integration Points & Extensions

### Decision Logic (`decision_node_impl.py`)
- Receives SKU data and 7-day forecast; outputs action recommendation.
- Check `quantity < threshold` and compare forecast against buffer stock.
- Return dict with keys: `reorder_required` (bool), `order_quantity`, `urgency_level`, `reasoning`.

### External Alerts (`app/routes/alerts.py`, `app/utils/telegram_bot.py`)
- Agent saves urgent alerts to DB; Telegram bot polls and sends messages.
- Alert message format: `{sku} | {product_name} | Action: {action} | Qty: {qty}`

### Feedback Loop (`app/routes/feedback.py`)
- Users can mark decisions as correct/incorrect; stored for future model tuning.
- Feedback records include original forecast, decision, actual outcome, user rating.

## Code Quality & Common Pitfalls

- **JSON parsing**: Always use `try_parse_json_from_text()` instead of raw `json.loads()`.
- **Session management**: Always call `db.close()` or use context manager; don't leave sessions open.
- **Logging**: Use module-level logger: `import logging; logger = logging.getLogger(__name__)`
- **Type hints**: Use `Dict[str, Any]`, `List[Dict]`, etc.; helps with code readability and IDE support.
- **Avoid hardcoded strings**: Constants like model names, table names, intervals are defined at module top.
- **Test fallbacks**: Mock Groq failures to ensure baseline logic works; see `forecast_node` baseline.

## File Structure Reference

```
app/
  agents/
    langgraph_flow.py       ← Main AgentController, cycle orchestration
    memory_manager.py       ← MemoryManager for persisting decisions
    reasoning_prompts.py    ← Prompt templates (format-ready)
    nodes/
      fetch_data_node.py    ← Stage 1: data retrieval
      forecast_node.py      ← Stage 2: LLM forecasting with fallback
      decision_node.py      ← Stage 3: decision logic proxy
      decision_node_impl.py ← Stage 3: actual decision implementation
      action_node.py        ← Stage 4: execute actions (orders, alerts)
      memory_node.py        ← Stage 5: persist run summary
  models/
    schemas.py              ← SQLAlchemy table definitions
    database.py             ← SessionLocal factory
  routes/
    agent.py                ← /agent/* endpoints & background loop
    inventory.py, sales.py, orders.py, alerts.py, feedback.py, memory.py
  utils/
    groq_utils.py           ← LLM queries, JSON extraction, error handling
    common.py               ← Model serialization helpers
    telegram_bot.py         ← Alert notifications
    scheduler.py            ← APScheduler integration (if used)
```

---

**Last Updated:** Nov 2025  
**Key Dependencies:** FastAPI, SQLAlchemy, LangGraph, Groq, Streamlit, Pydantic
