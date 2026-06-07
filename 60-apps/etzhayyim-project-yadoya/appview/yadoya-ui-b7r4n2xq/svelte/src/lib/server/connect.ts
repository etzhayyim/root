const APP_ID = 'yadoya';

export async function containerCall<T = unknown>(
	platform: App.Platform,
	service: string,
	method: string,
	body: unknown = {}
): Promise<T> {
	const container = platform.env.KOTODAMA.getByName(APP_ID);
	const resp = await container.fetch(`http://container/xrpc/${service}/${method}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});

	if (!resp.ok) {
		const text = await resp.text();
		throw new Error(`XRPC ${service}/${method} failed: ${resp.status} ${text}`);
	}

	return resp.json() as Promise<T>;
}
