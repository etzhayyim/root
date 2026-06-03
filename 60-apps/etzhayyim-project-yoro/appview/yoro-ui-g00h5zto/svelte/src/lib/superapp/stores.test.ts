import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import {
	currentTab,
	activeServiceApp,
	isActorOpen,
	openActor,
	closeActor,
	threadAppContext,
	threadUnreadCount,
	openTalkForApp,
	openSupportRoom,
} from './stores.js';
import type { SuperAppTab } from './stores.js';

describe('currentTab', () => {
	beforeEach(() => {
		currentTab.set('vibes');
	});

	it('defaults to vibes', () => {
		expect(get(currentTab)).toBe('vibes');
	});

	it('accepts primary tab IDs directly', () => {
		const tabs: SuperAppTab[] = ['vibes', 'search', 'talk', 'apps', 'profile'];
		for (const tab of tabs) {
			currentTab.set(tab);
			expect(get(currentTab)).toBe(tab);
		}
	});

	it('subscribe works correctly', () => {
		const values: string[] = [];
		const unsub = currentTab.subscribe((v) => values.push(v));
		currentTab.set('talk');
		currentTab.set('apps');
		unsub();
		currentTab.set('profile');
		expect(values).toEqual(['vibes', 'talk', 'apps']);
	});
});

describe('activeServiceApp / isActorOpen', () => {
	beforeEach(() => {
		closeActor();
	});

	it('defaults to null / false', () => {
		expect(get(activeServiceApp)).toBeNull();
		expect(get(isActorOpen)).toBe(false);
	});

	it('openActor sets nanoid and switches to apps tab', () => {
		currentTab.set('vibes');
		openActor('abc123');
		expect(get(activeServiceApp)).toBe('abc123');
		expect(get(isActorOpen)).toBe(true);
		expect(get(currentTab)).toBe('apps');
	});

	it('closeActor clears the active app', () => {
		openActor('abc123');
		closeActor();
		expect(get(activeServiceApp)).toBeNull();
		expect(get(isActorOpen)).toBe(false);
	});
});

describe('threadAppContext', () => {
	beforeEach(() => {
		threadAppContext.set(null);
		currentTab.set('vibes');
	});

	it('defaults to null', () => {
		expect(get(threadAppContext)).toBeNull();
	});

	it('openTalkForApp sets context and switches to talk tab', () => {
		openTalkForApp('nano1', 'TestApp', '🎯');
		expect(get(currentTab)).toBe('talk');
		const ctx = get(threadAppContext);
		expect(ctx).not.toBeNull();
		expect(ctx!.nanoid).toBe('nano1');
		expect(ctx!.name).toBe('TestApp');
		expect(ctx!.icon).toBe('🎯');
	});

	it('openTalkForApp with options includes defaultConvos', () => {
		openTalkForApp('nano2', 'App2', undefined, {
			defaultConvos: [{ id: 'ch1', name: 'general' }],
		});
		const ctx = get(threadAppContext);
		expect(ctx!.defaultConvos).toHaveLength(1);
		expect(ctx!.defaultConvos![0].id).toBe('ch1');
	});

	it('openSupportRoom sets etzhayyim support context', () => {
		openSupportRoom();
		expect(get(currentTab)).toBe('talk');
		const ctx = get(threadAppContext);
		expect(ctx!.nanoid).toBe('etzhayyim');
		expect(ctx!.name).toBe('Support');
		expect(ctx!.defaultConvos).toEqual([{ id: 'support', name: 'support' }]);
	});
});

describe('threadUnreadCount', () => {
	it('defaults to 0', () => {
		expect(get(threadUnreadCount)).toBe(0);
	});

	it('can be set and read', () => {
		threadUnreadCount.set(42);
		expect(get(threadUnreadCount)).toBe(42);
		threadUnreadCount.set(0);
	});
});
