<p align="center">
  <h1 align="center">KuroWatch</h1>
  <p align="center">Self-hosted anime/manga/manhwa/game tracking, discovery & download platform</p>
</p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-v1.2--STABLE%20%2097.6%25%20matched-brightgreen">
  <img alt="License" src="https://img.shields.io/github/license/KuroShinHQ/kurowatch">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.1.0-009688">
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

# Configure
cp backend/config.json.example backend/config.json  # Edit with your API keys

# Run
cd backend && python main.py
# Access at http://localhost:8099
```

### Configuration

Edit `backend/config.json` with:
- AniList: no auth needed
- IGDB: Twitch Client ID + Secret
- TMDB: API key
- MangaDex: no auth needed
- VAPID keys: for web push notifications

## API Overview

17 routers under `/api`:
- `/api/content` — CRUD + discover
- `/api/download` — queue, start, cancel, WebSocket progress
- `/api/system` — health, status, domain management
- `/api/translate` — manga translation
- `/api/game-download` — FitGirl magnet links
- And more (episodes, sites, tags, settings, sync, push, analytics, ...)

## Status

**v1.2-STABLE** — 97.6% content matched (697/714). 17 contents accepted as sourceless (old Turkish series + niche films not available on any site).

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
