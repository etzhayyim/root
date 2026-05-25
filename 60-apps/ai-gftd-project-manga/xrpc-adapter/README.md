# manga XRPC Adapter

CF Worker that exposes the 12 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/app.etzhayyim.manga.createTitle` — register manga title
- `GET /xrpc/app.etzhayyim.manga.getTitle?titleId=...` — title + chapters
- `GET /xrpc/app.etzhayyim.manga.listTitles?limit=...&offset=...` — paginated titles
- `GET /xrpc/app.etzhayyim.manga.searchTitles?q=...` — keyword search
- `POST /xrpc/app.etzhayyim.manga.addTag` — add tag to title
- `POST /xrpc/app.etzhayyim.manga.createChapter` — create chapter
- `GET /xrpc/app.etzhayyim.manga.getChapter?chapterNum=...` — chapter + pages
- `GET /xrpc/app.etzhayyim.manga.listChapters?titleId=...` — chapters for title
- `POST /xrpc/app.etzhayyim.manga.publishChapter` — publish chapter
- `POST /xrpc/app.etzhayyim.manga.updateChapterStatus` — chapter workflow
- `POST /xrpc/app.etzhayyim.manga.submitFromNarou` — ingest from Narou
- `POST /xrpc/app.etzhayyim.manga.recordReadingProgress` — reading history

## Setup

```bash
cd 60-apps/ai-gftd-project-manga/xrpc-adapter
npm install
```

## Development

```bash
npm run dev
# Worker listens on http://localhost:8787
```

## Deploy

```bash
wrangler deploy
# Deploys to manga.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
