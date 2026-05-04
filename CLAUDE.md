# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iFlyCompass (REL2.4.2) is a multi-feature Flask web app with: chat rooms (WebSocket), novel reader (smart chapter parsing), NetEase Cloud Music player (intranet-cached), B站 video caching/playback, local video player, sticker marketplace, announcement system, Drop messaging, and user management with Passkey-based registration.

## Commands

```bash
pip install -r requirements.txt   # Install dependencies
python app.py                     # Run on http://127.0.0.1:5002
pyinstaller --onefile --name iFlyCompass app.py   # Package as EXE
```

No test suite exists. Testing is manual (browser + Postman + browser dev tools for WebSocket).

## Architecture

**Three-layer design:**

1. **`models/`** — SQLAlchemy ORM models. `User` (with `is_admin`/`is_super_admin` booleans), `ChatRoom`, `UserSticker`/`PackSticker`, `NovelReadingProgress`, `Announcement`/`UserAnnouncementStatus`, `DropMessage`/`DropSettings`/`DropBlacklist`, `VideoAccessControl`/`VideoAccessUser`.

2. **`utils/`** — Shared utilities. Key ones: `ncm_api.py` (unified `NCMAPIClient` class with global `ncm_client` singleton — the single entry point for all NetEase Cloud Music API calls), `music_cache.py` (music/cover caching only, no API logic), `chapter_parser.py` (V3.1 anchor-learning chapter detection), `novel_cache.py` (startup pre-scan cache), `system_settings.py` (YAML read/write for settings), `validators.py` (password/username/nickname validation).

3. **`modules/`** — Flask Blueprints (one package per feature: `auth`, `chat`, `novel`, `sticker`, `ncm`, `video`, `bili`, `main`, `settings`, `announcement`, `drop`). Each module has `__init__.py` (Blueprint definition), `routes.py` (page routes), `api.py` (JSON API routes). All Blueprints register at root (no `url_prefix`) — path prefixes like `/api/` and `/board/` are written directly in route decorators.

**Startup flow** (`app.py`): create directories → `create_app()` initializes Flask/SQLAlchemy/LoginManager/SocketIO → registers all 11 Blueprints → registers SocketIO events from `modules/chat/websocket.py` → runs raw SQLite migrations → initializes novel cache, system settings, and nav config.

**Configuration** (`config.py`): YAML-driven via `instance/config.yml`. Auto-creates with defaults on first run. `Config` class attributes are populated from YAML at import time. `get_config()` / `save_config()` read/write the YAML file directly.

**Frontend**: Jinja2 templates with Vue.js 2.x + Element UI. All CSS/JS/fonts are local (no CDN). `templates/base.html` is the base template.

**Authentication**: Flask-Login with permanent sessions (10-year default). `@login_required` decorator on protected routes. Admin/Super-admin checks are done inline by checking `current_user.is_admin` / `current_user.is_super_admin`. The first registered user automatically becomes super admin.

**Socket.IO**: Real-time chat via `flask-socketio` with `async_mode='threading'`. Event handlers in `modules/chat/websocket.py`.

**Database**: SQLite via SQLAlchemy. Migrations are hand-written in `app.py:run_migrations()` — checks for missing columns/tables with raw SQL and adds them. No Alembic.

**FFmpeg**: Bundled in `tools/ffmpeg/ffmpeg.exe` and `ffprobe.exe` (~100MB each). Used for B站 video audio/video merging after download.

## Important Notes

- `utils/ncm_service.py` is a leftover file from the REL2.4.2 NCM API refactoring. Nothing imports it. `utils/ncm_api.py` (the `NCMAPIClient` class) is the canonical NCM API module.
- `instance/`, `stickers/`, `temp/` are in `.gitignore`. Runtime data includes `temp/music/` (music cache), `temp/bili/` (B站 video cache), and `instance/novels/` (novel files).
- See `DEVELOPMENT.md` for detailed version history and per-release change logs.
