"""ASGI server — SSE streaming endpoint for browser-agent LangGraph."""

from __future__ import annotations

import json
from aiohttp import web

from .graph import browser_search_graph
from .state import BrowserSearchState


async def health(_: web.Request) -> web.Response:
    return web.json_response({'ok': True, 'app': 'browser-agent'})


async def search_stream(request: web.Request) -> web.StreamResponse:
    body = await request.json()
    query: str = body.get('query', '').strip()
    page_url: str = body.get('page_url', '')

    if not query:
        return web.json_response({'error': 'query required'}, status=400)

    resp = web.StreamResponse(headers={
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Access-Control-Allow-Origin': '*',
    })
    await resp.prepare(request)

    async def sse(data: dict) -> None:
        await resp.write(f'data: {json.dumps(data)}\n\n'.encode())

    state = BrowserSearchState(query=query, page_url=page_url)

    try:
        async for event in browser_search_graph.astream_events(state, version='v2'):
            name = event.get('name', '')
            kind = event.get('event', '')

            # phase transitions
            if kind == 'on_chain_start':
                phase_map = {
                    'plan_queries': 'planning',
                    'search_web': 'searching',
                    'scrape_pages': 'scraping',
                    'synthesize': 'synthesizing',
                    'quality_check': 'done',
                }
                if name in phase_map:
                    await sse({'type': 'phase', 'phase': phase_map[name]})

            # emit sources as they are scraped
            elif kind == 'on_chain_end' and name == 'scrape_pages':
                output = event.get('data', {}).get('output', {})
                for r in output.get('scraped_contents', []):
                    url = r.url if hasattr(r, 'url') else r['url']
                    await sse({'type': 'source', 'url': url})

            # stream synthesis output token by token
            elif kind == 'on_chat_model_stream' and event.get('tags') and 'synthesize' in str(event.get('tags', [])):
                chunk = event.get('data', {}).get('chunk')
                if chunk and hasattr(chunk, 'content') and chunk.content:
                    await sse({'type': 'token', 'token': chunk.content})

            # emit final sections
            elif kind == 'on_chain_end' and name == 'synthesize':
                output = event.get('data', {}).get('output', {})
                for sec in output.get('sections', []):
                    await sse({'type': 'section', 'title': sec.get('title', ''), 'content': sec.get('content', '')})

    except Exception as e:
        await sse({'type': 'error', 'message': str(e)})

    await resp.write(b'data: [DONE]\n\n')
    return resp


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get('/health', health)
    app.router.add_post('/search', search_stream)
    return app


app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', '8000'))
    web.run_app(app, host='0.0.0.0', port=port)
