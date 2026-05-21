# manga XRPC Adapter

CF Worker that exposes the 12 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/ai.gftd.manga.createTitle` — register manga title
- `GET /xrpc/ai.gftd.manga.getTitle?titleId=...` — title + chapters
- `GET /xrpc/ai.gftd.manga.listTitles?limit=...&offset=...` — paginated titles
- `GET /xrpc/ai.gftd.manga.searchTitles?q=...` — keyword search
- `POST /xrpc/ai.gftd.manga.addTag` — add tag to title
- `POST /xrpc/ai.gftd.manga.createChapter` — create chapter
- `GET /xrpc/ai.gftd.manga.getChapter?chapterNum=...` — chapter + pages
- `GET /xrpc/ai.gftd.manga.listChapters?titleId=...` — chapters for title
- `POST /xrpc/ai.gftd.manga.publishChapter` — publish chapter
- `POST /xrpc/ai.gftd.manga.updateChapterStatus` — chapter workflow
- `POST /xrpc/ai.gftd.manga.submitFromNarou` — ingest from Narou
- `POST /xrpc/ai.gftd.manga.recordReadingProgress` — reading history

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
