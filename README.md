<p align="center">
  <h1 align="center">KuroWatch</h1>
  <p align="center">Self-hosted anime/manga/manhwa/game tracking, discovery & download platform</p>
</p>

```text
                      .
        ╲          \|/          ╱
         ╲─────────┴─────────╱
               ┌─────────┐
               │  (o.)   │      <- gozcu chibi + donen radar (menu ayni figur)
               └─────────┘
              ╱▔▔▔▔▔▔▔▔▔▔▔╲
             ███████████████
```

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-v1.2--STABLE%20%2097.6%25%20matched-brightgreen">
  <img alt="License" src="https://img.shields.io/github/license/KuroShinHQ/kurowatch">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="Version" src="https://img.shields.io/badge/app-v0.1.0-009688">
</p>

---

## Overview

**KuroWatch** is a self-hosted media tracking and download platform for anime, manga, manhwa, games, TV series, and movies. It features a FastAPI backend with 17 API routers, 9 metadata scrapers (AniList, MAL, IGDB, MangaDex, TMDB, FitGirl, and custom site parsers), a PWA frontend, and a Chrome browser extension. Currently tracking **714 items with 97.6% source coverage** (697/714 matched).

## Key Features

- **Multi-type tracking** — anime, manga, manhwa, games, series, movies, cartoons
- **9 scrapers** — AniList (GraphQL), MAL (OAuth2), IGDB (games), MangaDex, TMDB (film/series), FitGirl (repacks), custom site parsers
- **Download engine** — yt-dlp for video, gallery-dl for manga, FitGirl magnet links, WebSocket progress tracking
- **PWA frontend** — standalone installable web app with Tailwind, i18n (EN/TR), service worker
- **Chrome extension** — bridges Crunchyroll, DiziWatch, MangaDex, Tranimaci, Tranimeizle
- **Domain health monitor** — 24h scheduler, Cloudflare detection, auto-dead-site flagging
- **Auto-repair** — domain finder, URL pattern matching, alternative site discovery
- **Intro/outro detection** — chromaprint audio fingerprinting (FAZ-4)
- **Manga translation** — manga-image-translator integration (GPU-only, FAZ-5)
- **Web Push notifications** — VAPID-based push for new episodes

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0 async, aiosqlite, APScheduler |
| Scraping | httpx, curl-cffi (TLS impersonation), BeautifulSoup, Playwright |
| Downloads | yt-dlp, gallery-dl, aria2, WebSockets |
| Frontend | Vanilla JS SPA, Tailwind CSS, PWA (service worker + manifest) |
| Extension | Chrome Extension Manifest V3 |
| Testing | pytest, E2E suite |
| Deployment | Docker, docker-compose |

## Project Structure

```
kurowatch/
├── backend/
│   ├── main.py              # FastAPI app (port 8099), 17 routers
│   ├── database.py           # Async SQLAlchemy + aiosqlite
│   ├── models.py             # ORM: Content, Site, Episode, Tag
│   ├── routers/              # 17 API routers (content, download, system, ...)
│   ├── scraper/              # AniList, MAL, IGDB, MangaDex, TMDB, FitGirl, parsers
│   ├── downloader/           # stream_finder, anime, manga, manager, integrity
│   ├── analyzer/             # chromaprint intro/outro detection
│   ├── services/             # domain_health, domain_finder, db_updater, ...
│   ├── translator/           # manga-image-translator wrapper
│   ├── scripts/              # migration & maintenance scripts
│   └── tools/                # content_health, url_ping
├── frontend/                 # PWA SPA (app.js, player.js, Tailwind, i18n)
├── extension/                # Chrome extension (content scripts, popup)
├── tests/                    # pytest E2E suite
├── docs/                     # DEVAM.md, YAPI.md, FEATURE_MAP.md, archive/
└── docker-compose.yml        # Single-container deployment
```

## Installation

### Quick Start (Docker)

```bash
git clone https://github.com/KuroShinHQ/kurowatch.git
cd kurowatch
docker-compose up -d
# Access at http://localhost:8099
```

### Manual Setup

```bash
git clone https://github.com/KuroShinHQ/kurowatch.git
cd kurowatch
pip install -r backend/requirements.txt

# Run from the REPO ROOT (main.py has no __main__ entrypoint)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8099
# Access at http://localhost:8099
```

### Windows One-Click Launcher

| File | What it does |
|------|-------------|
| `kurowatch.bat` | Single entry point (TEK-BAT policy): TUI control menu (`kurowatch_menu.py`) — backend+frontend start, port cleanup, URL manager, accepts a menu number as argument (e.g. `kurowatch.bat 4`). The frontend is served by the FastAPI backend itself — no separate static server needed. |

### Configuration

The backend runs with **zero config** — `backend/config.json` is optional and
gitignored (`config.py` returns `{}` when it is missing). Create it only to
override defaults:

```json
{
  "igdb_client_id": "...",
  "igdb_client_secret": "...",
  "tmdb_api_key": "...",
  "max_concurrent_downloads": 2,
  "default_quality": "720p"
}
```

- AniList & MangaDex: no auth needed
- IGDB: Twitch Client ID + Secret
- TMDB: API key
- VAPID keys: auto-generated on first push use (see `backend/push_manager.py`)

> **Docker note:** `docker-compose.yml` mounts `./config.json` from the repo
> root. Since it is gitignored, create the file before `docker-compose up -d`
> — otherwise Docker creates an empty *directory* named `config.json`.

## API Overview

17 routers under `/api`:
- `/api/content` — CRUD + discover
- `/api/download` — queue, start, cancel, WebSocket progress
- `/api/system` — health, status, domain management
- `/api/translate` — manga translation
- `/api/game-download` — FitGirl magnet links
- And more (episodes, sites, tags, settings, sync, push, analytics, ...)

## Screenshots

> Screenshots coming soon. The PWA frontend includes a Netflix-style discovery grid,
> detail pages with metadata + cover art, a download manager with WebSocket progress,
> and a Chrome extension popup for in-browser content bridging.

## Roadmap

- [x] **FAZ-1**: Core tracking + AniList/MAL/IGDB scrapers
- [x] **FAZ-2**: System health + domain management
- [x] **FAZ-3**: Download engine (yt-dlp, gallery-dl, FitGirl)
- [x] **FAZ-4**: Intro/outro detection (chromaprint)
- [x] **FAZ-5**: Manga translation (manga-image-translator, GPU-only)
- [ ] **FAZ-6**: Mobile companion app
- [ ] **FAZ-7**: Multi-user support

## Status

**v1.2-STABLE** — 97.6% content matched (697/714). 17 contents accepted as sourceless (old Turkish series + niche films not available on any site).

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
