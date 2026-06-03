export async function browserCall<T = unknown>(
	service: string,
	method: string,
	body: unknown = {}
): Promise<T> {
	const resp = await fetch(`/xrpc/${service}/${method}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});

	if (!resp.ok) {
		const text = await resp.text();
		throw new Error(`${service}/${method} failed: ${resp.status} ${text}`);
	}

	return resp.json() as Promise<T>;
}
