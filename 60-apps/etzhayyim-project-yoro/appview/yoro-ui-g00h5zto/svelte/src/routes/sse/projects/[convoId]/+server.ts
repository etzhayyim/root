import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params, url }) => {
	const convoId = params.convoId;
	const since = Number(url.searchParams.get('since') || 0);
	const cursor = Number.isFinite(since) && since > 0 ? since : Date.now() - 5000;
	const encoder = new TextEncoder();
	const stream = new ReadableStream({
		start(controller) {
			controller.enqueue(encoder.encode(`event: open\ndata: ${JSON.stringify({ convoId, cursor })}\n\n`));
			controller.enqueue(encoder.encode(`: yoro-sveltekit-bff ${Date.now()}\n\n`));
			controller.close();
		}
	});
	return new Response(stream, {
		headers: {
			'content-type': 'text/event-stream; charset=utf-8',
			'cache-control': 'no-cache, no-transform',
			connection: 'keep-alive',
			'x-accel-buffering': 'no'
		}
	});
};
