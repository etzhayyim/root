import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

const mockCreateATConvo = vi.fn().mockResolvedValue({ convoId: 'mock-convo-id' });
const mockSendATMessage = vi.fn().mockResolvedValue(undefined);

vi.mock('$lib/atproto-agent', () => ({
	createConvo: (...args: any[]) => mockCreateATConvo(...args),
	sendProjectMessage: (...args: any[]) => mockSendATMessage(...args),
}));

import {
	formatContact, formatSms, isAndroidDeviceImportAvailable,
	getDeviceImportPermissionStatus, chunk, requestDeviceImportPermissions,
	importContactsToAT, importSmsToAT,
	// @internal test helpers
	_resetCachesForTesting, _setAndroidDataImportForTesting,
	withImportConvo, createImportConvo, sendImportHeader, sendImportNotice,
	getImportConvoId, importConvoKey,
} from './device-import.js';

// ── localStorage mock ──
const store: Record<string, string> = {};
const localStorageMock = {
	getItem: (key: string) => store[key] ?? null,
	setItem: (key: string, val: string) => { store[key] = val; },
	removeItem: (key: string) => { delete store[key]; },
};
if (typeof globalThis.localStorage === 'undefined') {
	(globalThis as any).localStorage = localStorageMock;
}

describe('formatContact', () => {
	it('formats contacts with phones and emails', () => {
		expect(formatContact({
			id: '1', displayName: 'Jane Doe',
			phoneNumbers: ['+81-90-0000-0000'], emails: ['jane@example.com'],
		})).toBe('Jane Doe\nPhones: +81-90-0000-0000\nEmails: jane@example.com');
	});

	it('formats contact with empty phone and email lists', () => {
		const result = formatContact({ id: '2', displayName: 'No Contact Info', phoneNumbers: [], emails: [] });
		expect(result).toBe('No Contact Info');
		expect(result).not.toContain('Phones:');
		expect(result).not.toContain('Emails:');
	});

	it('formats contact with no name as "(no name)"', () => {
		expect(formatContact({ id: '3', displayName: '', phoneNumbers: ['+1-555-0100'], emails: [] }))
			.toBe('(no name)\nPhones: +1-555-0100');
	});

	it('formats contact with multiple phones and emails', () => {
		expect(formatContact({
			id: '4', displayName: 'Multi',
			phoneNumbers: ['+1', '+2', '+3'], emails: ['a@x.com', 'b@x.com'],
		})).toBe('Multi\nPhones: +1, +2, +3\nEmails: a@x.com, b@x.com');
	});
});

describe('formatSms', () => {
	it('formats sms with type, timestamp, and body', () => {
		expect(formatSms({ id: 's1', address: '+1', body: 'hello', timestamp: 1710000000000, type: 'inbox' }))
			.toContain('[INBOX] +1');
	});

	it('formats sent SMS with SENT label', () => {
		const result = formatSms({ id: 's2', address: '+1', body: 'out', timestamp: 1710000000000, type: 'sent' });
		expect(result).toContain('[SENT]');
	});

	it('formats SMS timestamp as ISO string', () => {
		const ts = 1710000000000;
		expect(formatSms({ id: 's3', address: '+1', body: 'test', timestamp: ts, type: 'inbox' }))
			.toContain(new Date(ts).toISOString());
	});

	it('formats SMS with empty body as "(empty)"', () => {
		expect(formatSms({ id: 's4', address: '+1', body: '', timestamp: 1710000000000, type: 'inbox' }))
			.toContain('(empty)');
	});

	it('formats SMS with whitespace-only body as "(empty)"', () => {
		expect(formatSms({ id: 's5', address: '+1', body: '   \n  ', timestamp: 1710000000000, type: 'inbox' }))
			.toContain('(empty)');
	});

	it('formats SMS with unknown sender as "(unknown sender)"', () => {
		expect(formatSms({ id: 's6', address: '', body: 'msg', timestamp: 1710000000000, type: 'inbox' }))
			.toContain('(unknown sender)');
	});

	it('formats SMS with non-finite timestamp without date line', () => {
		const result = formatSms({ id: 's7', address: '+1', body: 'no time', timestamp: NaN, type: 'inbox' });
		expect(result).not.toContain('Invalid');
		expect(result).toContain('[INBOX] +1');
		expect(result).toContain('no time');
	});
});

describe('chunk', () => {
	it('splits array into equal-sized batches', () => {
		expect(chunk([1, 2, 3, 4, 5, 6], 2)).toEqual([[1, 2], [3, 4], [5, 6]]);
	});

	it('handles last batch smaller than size', () => {
		expect(chunk([1, 2, 3, 4, 5], 3)).toEqual([[1, 2, 3], [4, 5]]);
	});

	it('returns empty array for empty input', () => {
		expect(chunk([], 5)).toEqual([]);
	});

	it('handles size larger than array', () => {
		expect(chunk([1, 2], 10)).toEqual([[1, 2]]);
	});

	it('with size 1 gives individual elements', () => {
		expect(chunk(['a', 'b', 'c'], 1)).toEqual([['a'], ['b'], ['c']]);
	});
});

describe('isAndroidDeviceImportAvailable', () => {
	afterEach(() => { delete (globalThis as any).Capacitor; });

	it('returns false when Capacitor not available', () => {
		expect(isAndroidDeviceImportAvailable()).toBe(false);
	});

	it('returns true when Capacitor platform is android', () => {
		(globalThis as any).Capacitor = { getPlatform: () => 'android' };
		expect(isAndroidDeviceImportAvailable()).toBe(true);
	});

	it('returns false when Capacitor platform is ios', () => {
		(globalThis as any).Capacitor = { getPlatform: () => 'ios' };
		expect(isAndroidDeviceImportAvailable()).toBe(false);
	});

	it('returns false when getPlatform is not a function', () => {
		(globalThis as any).Capacitor = { getPlatform: 'web' };
		expect(isAndroidDeviceImportAvailable()).toBe(false);
	});
});

describe('getDeviceImportPermissionStatus', () => {
	it('returns denied on non-android', async () => {
		expect(await getDeviceImportPermissionStatus()).toEqual({ contacts: 'denied', sms: 'denied' });
	});
});

describe('importConvoKey', () => {
	it('returns contacts key for contacts', () => {
		expect(importConvoKey('contacts')).toBe('yoro.import.contacts.convoId');
	});

	it('returns sms key for sms', () => {
		expect(importConvoKey('sms')).toBe('yoro.import.sms.convoId');
	});
});

describe('getImportConvoId', () => {
	beforeEach(() => {
		localStorage.removeItem('yoro.import.contacts.convoId');
		localStorage.removeItem('yoro.import.sms.convoId');
	});

	it('returns empty when no convo stored', () => {
		expect(getImportConvoId('contacts')).toBe('');
		expect(getImportConvoId('sms')).toBe('');
	});

	it('returns stored convo id', () => {
		localStorage.setItem('yoro.import.contacts.convoId', 'cv-123');
		expect(getImportConvoId('contacts')).toBe('cv-123');
	});

	it('trims whitespace from stored id', () => {
		localStorage.setItem('yoro.import.sms.convoId', '  cv-456  ');
		expect(getImportConvoId('sms')).toBe('cv-456');
	});
});

describe('sendImportNotice', () => {
	beforeEach(() => { mockSendATMessage.mockClear(); });

	it('sends JSON notice via sendMessage', async () => {
		await sendImportNotice('cv-1', 'Hello test');
		expect(mockSendATMessage).toHaveBeenCalledWith('cv-1', JSON.stringify({ body: 'Hello test', msgtype: 'm.notice' }));
	});
});

describe('sendImportHeader', () => {
	beforeEach(() => { mockSendATMessage.mockClear(); });

	it('sends header with timestamp', async () => {
		await sendImportHeader('cv-1', 'Imported 5 contacts');
		expect(mockSendATMessage).toHaveBeenCalledTimes(1);
		const sentBody = JSON.parse(mockSendATMessage.mock.calls[0][1]);
		expect(sentBody.body).toContain('Imported 5 contacts');
		expect(sentBody.body).toContain('Imported at');
		expect(sentBody.msgtype).toBe('m.notice');
	});
});

describe('createImportConvo', () => {
	beforeEach(() => {
		mockCreateATConvo.mockClear();
		mockCreateATConvo.mockResolvedValue({ convoId: 'new-cv-id' });
		localStorage.removeItem('yoro.import.contacts.convoId');
		localStorage.removeItem('yoro.import.sms.convoId');
	});

	it('creates contacts convo and stores id', async () => {
		const id = await createImportConvo('contacts');
		expect(id).toBe('new-cv-id');
		expect(mockCreateATConvo).toHaveBeenCalledWith('Android Contacts Import', expect.objectContaining({
			kind: 'private',
		}));
		expect(localStorage.getItem('yoro.import.contacts.convoId')).toBe('new-cv-id');
	});

	it('creates sms convo and stores id', async () => {
		const id = await createImportConvo('sms');
		expect(id).toBe('new-cv-id');
		expect(mockCreateATConvo).toHaveBeenCalledWith('Android SMS Import', expect.objectContaining({
			kind: 'private',
			description: expect.stringContaining('SMS'),
		}));
		expect(localStorage.getItem('yoro.import.sms.convoId')).toBe('new-cv-id');
	});

	it('throws when createConvo returns no id', async () => {
		mockCreateATConvo.mockResolvedValue({ convoId: '' });
		await expect(createImportConvo('contacts')).rejects.toThrow('Failed to create AT convo');
	});
});

describe('withImportConvo', () => {
	beforeEach(() => {
		mockCreateATConvo.mockClear();
		mockCreateATConvo.mockResolvedValue({ convoId: 'wic-cv' });
		localStorage.removeItem('yoro.import.contacts.convoId');
		localStorage.removeItem('yoro.import.sms.convoId');
	});

	it('creates convo when none stored and runs work', async () => {
		const work = vi.fn().mockResolvedValue(undefined);
		const id = await withImportConvo('contacts', work);
		expect(id).toBe('wic-cv');
		expect(work).toHaveBeenCalledWith('wic-cv');
	});

	it('uses stored convo id when available', async () => {
		localStorage.setItem('yoro.import.contacts.convoId', 'existing-cv');
		const work = vi.fn().mockResolvedValue(undefined);
		const id = await withImportConvo('contacts', work);
		expect(id).toBe('existing-cv');
		expect(work).toHaveBeenCalledWith('existing-cv');
		expect(mockCreateATConvo).not.toHaveBeenCalled();
	});

	it('retries with new convo on work failure', async () => {
		localStorage.setItem('yoro.import.contacts.convoId', 'old-cv');
		let callCount = 0;
		const work = vi.fn().mockImplementation(async () => {
			callCount++;
			if (callCount === 1) throw new Error('work failed');
		});
		const id = await withImportConvo('contacts', work);
		expect(id).toBe('wic-cv');
		expect(work).toHaveBeenCalledTimes(2);
		// old convo id should be cleared
		expect(localStorage.getItem('yoro.import.contacts.convoId')).toBe('wic-cv');
	});
});

describe('importContactsToAT (mocked plugin)', () => {
	const mockPlugin = {
		getPermissionStatus: vi.fn().mockResolvedValue({ contacts: 'granted', sms: 'granted' }),
		requestImportPermissions: vi.fn().mockResolvedValue({ contacts: 'granted', sms: 'granted' }),
		getContacts: vi.fn().mockResolvedValue({
			contacts: [
				{ id: '1', displayName: 'Alice', phoneNumbers: ['+1-555-0001'], emails: ['alice@x.com'] },
				{ id: '2', displayName: '', phoneNumbers: [], emails: [] },
			],
		}),
		getSms: vi.fn().mockResolvedValue({
			messages: [
				{ id: 's1', address: '+1-555-0001', body: 'Hello', timestamp: 1710000000000, type: 'inbox' },
			],
			limit: 200,
		}),
	};

	beforeEach(() => {
		_resetCachesForTesting();
		(globalThis as any).Capacitor = { getPlatform: () => 'android' };
		_setAndroidDataImportForTesting(mockPlugin);
		mockCreateATConvo.mockClear().mockResolvedValue({ convoId: 'import-cv' });
		mockSendATMessage.mockClear();
		localStorage.removeItem('yoro.import.contacts.convoId');
		localStorage.removeItem('yoro.import.sms.convoId');
	});

	afterEach(() => {
		delete (globalThis as any).Capacitor;
		_resetCachesForTesting();
	});

	it('imports contacts and returns count (filters empty contacts)', async () => {
		const result = await importContactsToAT();
		expect(result.importedCount).toBe(1); // Only Alice has data
		expect(result.convoId).toBe('import-cv');
		expect(mockPlugin.getContacts).toHaveBeenCalled();
		expect(mockSendATMessage).toHaveBeenCalled();
	});

	it('imports SMS messages', async () => {
		const result = await importSmsToAT(100);
		expect(result.importedCount).toBe(1);
		expect(result.convoId).toBe('import-cv');
		expect(mockPlugin.getSms).toHaveBeenCalledWith({ limit: 100 });
	});

	it('imports all SMS messages by default', async () => {
		await importSmsToAT();
		expect(mockPlugin.getSms).toHaveBeenCalledWith({});
	});

	it('getDeviceImportPermissionStatus on android returns plugin status', async () => {
		const status = await getDeviceImportPermissionStatus();
		expect(status).toEqual({ contacts: 'granted', sms: 'granted' });
	});

	it('requestDeviceImportPermissions on android calls plugin', async () => {
		const status = await requestDeviceImportPermissions({ contacts: true });
		expect(status).toEqual({ contacts: 'granted', sms: 'granted' });
		expect(mockPlugin.requestImportPermissions).toHaveBeenCalledWith({ contacts: true });
	});
});

describe('requestDeviceImportPermissions error path', () => {
	it('throws on non-android', async () => {
		_resetCachesForTesting();
		delete (globalThis as any).Capacitor;
		await expect(requestDeviceImportPermissions({ contacts: true })).rejects.toThrow('only available on Android');
	});
});
