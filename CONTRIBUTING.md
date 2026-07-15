# Contributing to KuroWatch

Thank you for your interest in contributing to KuroWatch!

## Development Workflow

1. **Fork & Clone** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make changes** following the code style below
4. **Test**: run `pytest tests/` and verify no regressions
5. **Commit**: use conventional commit messages
6. **Push & PR**: open a Pull Request

## Code Style

- Python 3.10+ with type hints (`from typing import ...`)
- FastAPI endpoints: `async def` + `await` (no sync DB calls)
- SQLAlchemy 2.0 style: `Mapped[]`, `mapped_column()`, `selectinload()` for relations
- Frontend: vanilla JS (ES5-compatible for broader support), no build step required
- No comments unless explicitly requested

## Architecture Rules

1. **API endpoint** → write request/response Pydantic schema FIRST
2. **DB model** → write ORM class FIRST
3. **Then** implement router + scraper logic

## Common Pitfalls (Avoid)

- **N+1 queries** — use `selectinload()` on all relationships
- **Async/sync mix** — FastAPI `async def` endpoints must use `await` for DB calls
- **Import cycles** — `models.py` must not import from `routers/`
- **SQLite concurrency** — use `aiosqlite` async driver
- **CORS** — frontend may run on different port; CORS middleware is configured

## Testing

```bash
# Unit tests
pytest tests/ -v

# E2E tests
pytest tests/test_sohbet142_e2e.py -v

# Backend integrity
pytest tests/test_backend_integrity.py -v
```

## Adding a New Scraper

1. Create `backend/scraper/yoursite.py`
2. Implement the fetch function (async, returns structured data)
3. Register in `backend/scraper/sources.py`
4. Add URL patterns in `backend/services/url_patterns.py` if needed
5. Test with real requests (no mocks — use curl/log analysis)

## Commit Messages

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `scraper:` new/updated site parser
- `test:` test additions

## Security

- Never commit `backend/config.json` (contains API keys, VAPID keys)
- Never commit `memory/kurowatch.db` (contains user data)
- Never commit `cookies/` or credential files

## Issues

Report bugs via GitHub Issues. Include:
- Expected vs actual behavior
- Relevant log output
- Content ID if applicable
