# Development Plan: LMS Telegram Bot

## Overview

This document outlines the development plan for the LMS (Learning Management System) Telegram bot. The bot provides students with access to their academic information, including lab scores, course materials, and automated assistance powered by an LLM.

## Architecture Principles.

### Testable Handler Architecture (P0.1)

The core design principle is **separation of concerns**. Command handlers are pure functions that take input (command text, user context) and return output (response text). They have no knowledge of Telegram's API. This enables:

- **Offline testing** via `--test` mode without Telegram connection
- **Unit testing** handlers in isolation
- **Easy transport switching** (Telegram → Discord → Web API)

### Layered Structure

```
┌─────────────────────────────────────┐
│         Telegram Bot (aiogram)      │  ← Transport layer
├─────────────────────────────────────┤
│         Command Handlers            │  ← Business logic (testable)
├─────────────────────────────────────┤
│    Services (LMS API, LLM API)      │  ← External integrations
├─────────────────────────────────────┤
│         Configuration               │  ← Environment variables
└─────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Project Scaffold (Current Task)

Create the basic project structure with:
- `bot.py` — entry point with `--test` mode support
- `handlers/` — command handlers (start, help, health, labs, scores)
- `services/` — API client stubs for LMS and LLM
- `config.py` — environment variable loading from `.env.bot.secret`
- `pyproject.toml` — bot dependencies managed by `uv`

**Acceptance**: `uv run bot.py --test "/start"` prints response and exits 0.

### Phase 2: Backend Integration

Implement real API clients in `services/`:
- `LMSClient` — HTTP client for backend API (`/api/labs`, `/api/scores`)
- `LLMClient` — OpenRouter API client for natural language queries
- Error handling, retries, and timeout configuration

Handlers will use these services to fetch real data instead of returning placeholders.

### Phase 3: Intent Routing (Task 3)

Implement natural language understanding:
- User messages like "what labs are available" are routed to appropriate handlers
- LLM-based intent classification
- Fallback to help message for unrecognized intents

### Phase 4: Deployment

- Docker containerization for the bot
- Production configuration (logging, monitoring)
- CI/CD pipeline for automated deployment

## Test Mode Specification

The `--test` flag enables offline verification:

```bash
cd bot
uv run bot.py --test "/start"           # Welcome message
uv run bot.py --test "/help"            # Command list
uv run bot.py --test "/health"          # Backend health check
uv run bot.py --test "/scores lab-04"   # Student scores
uv run bot.py --test "what labs exist"  # Natural language query
```

**Requirements**:
- Prints response to stdout
- Exits with code 0
- No Telegram connection required
- Reads config from `.env.bot.secret`

## File Structure

```
bot/
├── bot.py              # Entry point (Telegram + --test mode)
├── config.py           # Configuration loading
├── pyproject.toml      # Dependencies
├── PLAN.md             # This file
├── handlers/
│   ├── __init__.py
│   ├── base.py         # Base handler interface
│   ├── start.py        # /start command
│   ├── help.py         # /help command
│   ├── health.py       # /health command
│   ├── labs.py         # /labs command
│   └── scores.py       # /scores command
└── services/
    ├── __init__.py
    ├── lms_client.py   # LMS API client
    └── llm_client.py   # LLM API client
```

## Dependencies

- `aiogram>=3.20` — Telegram Bot API framework
- `httpx==0.28.1` — Async HTTP client for API calls
- `pydantic-settings==2.12.0` — Configuration management

## Next Steps

1. Complete scaffold with placeholder handlers
2. Verify `--test` mode works for all commands
3. Implement real API clients in Phase 2
4. Add intent routing in Phase 3
