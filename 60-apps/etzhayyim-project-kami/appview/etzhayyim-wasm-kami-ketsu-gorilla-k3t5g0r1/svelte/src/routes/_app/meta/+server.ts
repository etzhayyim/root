import { json } from '@sveltejs/kit';

export function GET() {
	return json({
		nanoid: 'k3t5g0r1',
		name: 'kami-ketsu-gorilla',
		version: 'v1.4.0',
		performerType: 'service',
		uiType: 'iframe',
	}, {
		headers: { 'Access-Control-Allow-Origin': '*' },
	});
}
