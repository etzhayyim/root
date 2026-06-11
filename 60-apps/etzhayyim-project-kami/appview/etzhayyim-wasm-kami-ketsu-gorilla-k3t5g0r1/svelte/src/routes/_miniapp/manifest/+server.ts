import { json } from '@sveltejs/kit';

export function GET() {
	return json({
		nanoid: 'k3t5g0r1',
		name: 'kami-ketsu-gorilla',
		displayName: 'Goriketsu Dash!!',
		ui: 'iframe',
		performerType: 'service',
		category: 'game',
		heroSurface: 'iframe',
		guestAccess: true,
		version: 'v1.4.0',
	}, {
		headers: { 'Access-Control-Allow-Origin': '*' },
	});
}
