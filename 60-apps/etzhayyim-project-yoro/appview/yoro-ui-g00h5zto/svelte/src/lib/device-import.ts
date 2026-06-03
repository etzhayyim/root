	import { createConvo, sendProjectMessage, atProcedure } from '$lib/atproto-agent';

type PermissionStatus = 'prompt' | 'denied' | 'granted';

export interface DeviceImportPermissionStatus {
	contacts: PermissionStatus;
	sms: PermissionStatus;
}

export interface DeviceContact {
	id: string;
	displayName: string;
	phoneNumbers: string[];
	emails: string[];
}

export interface DeviceSmsMessage {
	id: string;
	address: string;
	body: string;
	timestamp: number;
	type: string;
}

interface AndroidDataImportPlugin {
	getPermissionStatus(): Promise<DeviceImportPermissionStatus>;
	requestImportPermissions(options: { contacts?: boolean; sms?: boolean }): Promise<DeviceImportPermissionStatus>;
	getContacts(): Promise<{ contacts: DeviceContact[] }>;
	getSms(options: { limit?: number }): Promise<{ messages: DeviceSmsMessage[]; limit: number }>;
}

const CONTACTS_CONVO_KEY = 'yoro.import.contacts.convoId';
const SMS_CONVO_KEY = 'yoro.import.sms.convoId';
const CONTACT_BATCH_SIZE = 25;
const SMS_BATCH_SIZE = 50;

type CapacitorCoreLike = {
	Capacitor: {
		getPlatform(): string;
	};
	registerPlugin<T>(name: string): T;
};

let capacitorCorePromise: Promise<CapacitorCoreLike | null> | null = null;
let androidDataImportPromise: Promise<AndroidDataImportPlugin | null> | null = null;

/** @internal Reset module-level caches for testing */
export function _resetCachesForTesting(): void {
	capacitorCorePromise = null;
	androidDataImportPromise = null;
}

/** @internal Inject a mock plugin for testing */
export function _setAndroidDataImportForTesting(plugin: AndroidDataImportPlugin): void {
	androidDataImportPromise = Promise.resolve(plugin);
}

function getCapacitorGlobalPlatform(): string {
	const platform = (globalThis as { Capacitor?: { getPlatform?: () => string } }).Capacitor?.getPlatform;
	return typeof platform === 'function' ? platform() : 'web';
}

function loadCapacitorCore(): Promise<CapacitorCoreLike | null> {
	if (!capacitorCorePromise) {
		const importer = new Function('return import("@capacitor/core")') as () => Promise<CapacitorCoreLike>;
		capacitorCorePromise = importer().catch((_err) => null);
	}
	return capacitorCorePromise;
}

async function getAndroidDataImport(): Promise<AndroidDataImportPlugin> {
	if (!isAndroidDeviceImportAvailable()) {
		throw new Error('Device import is only available on Android');
	}
	if (!androidDataImportPromise) {
		androidDataImportPromise = loadCapacitorCore().then((mod) => {
			if (!mod) {
				throw new Error('@capacitor/core is unavailable');
			}
			return mod.registerPlugin<AndroidDataImportPlugin>('AndroidDataImport');
		});
	}
	const plugin = await androidDataImportPromise;
	if (!plugin) {
		throw new Error('AndroidDataImport plugin is unavailable');
	}
	return plugin;
}

export function isAndroidDeviceImportAvailable(): boolean {
	return getCapacitorGlobalPlatform() === 'android';
}

export async function getDeviceImportPermissionStatus(): Promise<DeviceImportPermissionStatus> {
	if (!isAndroidDeviceImportAvailable()) {
		return { contacts: 'denied', sms: 'denied' };
	}
	const androidDataImport = await getAndroidDataImport();
	return androidDataImport.getPermissionStatus();
}

export async function requestDeviceImportPermissions(options: { contacts?: boolean; sms?: boolean }): Promise<DeviceImportPermissionStatus> {
	const androidDataImport = await getAndroidDataImport();
	return androidDataImport.requestImportPermissions(options);
}

export async function importContactsToAT(): Promise<{ convoId: string; importedCount: number }> {
	const androidDataImport = await getAndroidDataImport();
	const { contacts } = await androidDataImport.getContacts();
	const importedContacts = contacts.filter((contact) => contact.displayName || contact.phoneNumbers.length > 0 || contact.emails.length > 0);
	const convoId = await withImportConvo('contacts', async (targetConvoId) => {
		await sendImportHeader(targetConvoId, `Imported ${importedContacts.length} contacts from this Android device.`);
		for (const batch of chunk(importedContacts, CONTACT_BATCH_SIZE)) {
			const body = batch.map(formatContact).join('\n\n');
			await sendImportNotice(targetConvoId, body);
		}
	});
	return { convoId, importedCount: importedContacts.length };
}

/**
 * Write each SMS as an `com.etzhayyim.apps.smishing.smsMessage` AT Record so the
 * smishing-core worker can subscribe and run the detection pipeline.
 * The sender address is SHA-256 hashed (16-hex prefix) for privacy.
 */
export async function importSmsAsRecords(limit?: number): Promise<{ importedCount: number }> {
	const androidDataImport = await getAndroidDataImport();
	const { messages } = typeof limit === 'number'
		? await androidDataImport.getSms({ limit })
		: await androidDataImport.getSms({});
	const importedMessages = messages.filter((m) => m.address || m.body);
	const now = new Date().toISOString();
	for (const batch of chunk(importedMessages, 10)) {
		await Promise.all(
			batch.map(async (message) => {
				const urls = extractSmsUrls(message.body ?? '');
				const record = {
					senderHash: await hashAddress(message.address ?? ''),
					body: message.body ?? '',
					timestamp: Number.isFinite(message.timestamp)
						? new Date(message.timestamp).toISOString()
						: now,
					type: message.type,
					hasUrls: urls.length > 0,
					urlCount: urls.length,
					importedAt: now,
				};
				await atProcedure('com.atproto.repo.createRecord', {
					collection: 'com.etzhayyim.apps.smishing.smsMessage',
					record,
				});
			}),
		);
	}
	return { importedCount: importedMessages.length };
}

/** @internal */
export function extractSmsUrls(text: string): string[] {
	return text.match(/https?:\/\/[^\s]+/g) ?? [];
}

/** @internal */
export async function hashAddress(address: string): Promise<string> {
	const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(address));
	return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
}

export async function importSmsToAT(limit?: number): Promise<{ convoId: string; importedCount: number }> {
	const androidDataImport = await getAndroidDataImport();
	const { messages } = typeof limit === 'number'
		? await androidDataImport.getSms({ limit })
		: await androidDataImport.getSms({});
	const importedMessages = messages.filter((message) => message.address || message.body);
	const convoId = await withImportConvo('sms', async (targetConvoId) => {
		await sendImportHeader(targetConvoId, `Imported ${importedMessages.length} SMS messages from this Android device.`);
		for (const batch of chunk(importedMessages, SMS_BATCH_SIZE)) {
			const body = batch.map(formatSms).join('\n\n');
			await sendImportNotice(targetConvoId, body);
		}
	});
	return { convoId, importedCount: importedMessages.length };
}

export function formatContact(contact: DeviceContact): string {
	const lines = [contact.displayName || '(no name)'];
	if (contact.phoneNumbers.length > 0) {
		lines.push(`Phones: ${contact.phoneNumbers.join(', ')}`);
	}
	if (contact.emails.length > 0) {
		lines.push(`Emails: ${contact.emails.join(', ')}`);
	}
	return lines.join('\n');
}

export function formatSms(message: DeviceSmsMessage): string {
	const label = message.type.toUpperCase();
	const address = message.address || '(unknown sender)';
	const timestamp = Number.isFinite(message.timestamp) ? new Date(message.timestamp).toISOString() : '';
	const body = message.body?.trim() || '(empty)';
	return [`[${label}] ${address}`, timestamp, body].filter(Boolean).join('\n');
}

/** @internal exported for testing */
export function chunk<T>(items: T[], size: number): T[][] {
	const chunks: T[][] = [];
	for (let index = 0; index < items.length; index += size) {
		chunks.push(items.slice(index, index + size));
	}
	return chunks;
}

/** @internal exported for testing */
export async function withImportConvo(
	kind: 'contacts' | 'sms',
	work: (convoId: string) => Promise<void>,
): Promise<string> {
	let convoId = getImportConvoId(kind);
	if (!convoId) {
		convoId = await createImportConvo(kind);
	}
	try {
		await work(convoId);
		return convoId;
	} catch (error) {
		if (getImportConvoId(kind) === convoId) {
			localStorage.removeItem(importConvoKey(kind));
		}
		if (!convoId) throw error;
		const retryConvoId = await createImportConvo(kind);
		await work(retryConvoId);
		return retryConvoId;
	}
}

/** @internal exported for testing */
export async function createImportConvo(kind: 'contacts' | 'sms'): Promise<string> {
	const result = await createConvo(
		kind === 'contacts' ? 'Android Contacts Import' : 'Android SMS Import',
		{
			kind: 'private',
			description: kind === 'contacts'
				? 'Imported contacts from this Android device via YORO.'
				: 'Imported SMS messages from this Android device via YORO.',
		},
	);
	const convoId = result.convoId;
	if (!convoId) {
		throw new Error(`Failed to create AT convo for ${kind} import`);
	}
	localStorage.setItem(importConvoKey(kind), convoId);
	return convoId;
}

/** @internal exported for testing */
export async function sendImportHeader(convoId: string, body: string): Promise<void> {
	await sendImportNotice(convoId, `${body}\nImported at ${new Date().toISOString()}`);
}

/** @internal exported for testing */
export async function sendImportNotice(convoId: string, body: string): Promise<void> {
	await sendProjectMessage(convoId, JSON.stringify({ body, msgtype: 'm.notice' }));
}

/** @internal exported for testing */
export function getImportConvoId(kind: 'contacts' | 'sms'): string {
	if (typeof localStorage === 'undefined') return '';
	return localStorage.getItem(importConvoKey(kind))?.trim() ?? '';
}

/** @internal exported for testing */
export function importConvoKey(kind: 'contacts' | 'sms'): string {
	return kind === 'contacts' ? CONTACTS_CONVO_KEY : SMS_CONVO_KEY;
}
