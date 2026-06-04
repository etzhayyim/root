/**
 * line-notification — bridge to the Android-side {@code LineNotificationPlugin}.
 *
 * Reads LINE notifications captured by the {@code LineNotificationListener}
 * NotificationListenerService and forwards them to malak via XRPC.
 *
 * The user must one-time grant the system "Notification access" permission via
 * Settings (the {@link openLineNotificationSettings} helper opens that page).
 *
 * Returns a no-op stub on web / iOS so call sites can render the same UI.
 */

import { atProcedure } from '$lib/atproto-agent';

export interface LineNotification {
	id: number;
	postTimeMs: number;
	key: string;
	tag: string;
	title: string;
	text: string;
	bigText: string;
	subText: string;
	category: string;
}

export interface LineNotificationStatus {
	accessGranted: boolean;
	connected: boolean;
	bufferSize: number;
}

interface LineNotificationPlugin {
	getStatus(): Promise<LineNotificationStatus>;
	openSettings(): Promise<void>;
	drain(): Promise<{ notifications: LineNotification[]; count: number }>;
	snapshot(): Promise<{ notifications: LineNotification[]; count: number }>;
}

type CapacitorCoreLike = {
	Capacitor: { getPlatform(): string };
	registerPlugin<T>(name: string): T;
};

let pluginPromise: Promise<LineNotificationPlugin | null> | null = null;

async function loadPlugin(): Promise<LineNotificationPlugin | null> {
	if (pluginPromise) return pluginPromise;

	pluginPromise = (async () => {
		const platform = (globalThis as { Capacitor?: { getPlatform?: () => string } }).Capacitor?.getPlatform;
		if (typeof platform !== 'function' || platform() !== 'android') {
			return null;
		}
		try {
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			const mod = (await import(/* @vite-ignore */ '@capacitor/core')) as unknown as CapacitorCoreLike;
			return mod.registerPlugin<LineNotificationPlugin>('LineNotification');
		} catch {
			return null;
		}
	})();
	return pluginPromise;
}

export async function isAvailable(): Promise<boolean> {
	const p = await loadPlugin();
	return p !== null;
}

export async function getLineNotificationStatus(): Promise<LineNotificationStatus> {
	const p = await loadPlugin();
	if (!p) return { accessGranted: false, connected: false, bufferSize: 0 };
	return p.getStatus();
}

export async function openLineNotificationSettings(): Promise<void> {
	const p = await loadPlugin();
	if (!p) return;
	await p.openSettings();
}

export async function drainLineNotifications(): Promise<LineNotification[]> {
	const p = await loadPlugin();
	if (!p) return [];
	const res = await p.drain();
	return res.notifications;
}

export async function snapshotLineNotifications(): Promise<LineNotification[]> {
	const p = await loadPlugin();
	if (!p) return [];
	const res = await p.snapshot();
	return res.notifications;
}

/**
 * Drain pending LINE notifications and forward each to malak via the
 * `com.etzhayyim.apps.malak.ingestTrapMessage` XRPC procedure.
 *
 * `tlp` defaults to AMBER. Notifications with empty title+text are skipped.
 */
export async function forwardLineNotificationsToMalak(
	opts: { tlp?: string; recipient?: string } = {}
): Promise<{ sent: number; skipped: number; errors: number }> {
	const items = await drainLineNotifications();
	let sent = 0;
	let skipped = 0;
	let errors = 0;

	for (const n of items) {
		const body = [n.title, n.subText, n.bigText || n.text].filter(Boolean).join('\n').trim();
		if (!body) {
			skipped++;
			continue;
		}
		try {
			await atProcedure('com.etzhayyim.apps.malak.ingestTrapMessage', {
				trapKind: 'email',
				provider: 'line',
				recipient: opts.recipient ?? 'line:device',
				providerMessageId: n.key || `${n.id}`,
				sender: n.title || 'line:unknown',
				subject: '',
				bodyPreview: body.slice(0, 2000),
				receivedAt: new Date(n.postTimeMs).toISOString(),
				headersJson: '',
				urls: extractUrls(body),
				tlp: opts.tlp ?? 'AMBER'
			});
			sent++;
		} catch {
			errors++;
		}
	}

	return { sent, skipped, errors };
}

function extractUrls(body: string): string[] {
	const re = /https?:\/\/[^\s<>"']+/gi;
	const out = new Set<string>();
	let m: RegExpExecArray | null;
	while ((m = re.exec(body)) !== null) {
		out.add(m[0]);
		if (out.size >= 50) break;
	}
	return [...out];
}
