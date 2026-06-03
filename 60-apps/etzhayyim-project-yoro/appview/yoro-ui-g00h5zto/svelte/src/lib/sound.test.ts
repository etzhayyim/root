import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock AudioContext since vitest runs in Node (no Web Audio API)
class MockOscillator {
	type = 'sine';
	frequency = { setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() };
	connect = vi.fn().mockReturnThis();
	start = vi.fn();
	stop = vi.fn();
}

class MockGainNode {
	gain = { setValueAtTime: vi.fn(), linearRampToValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() };
	connect = vi.fn().mockReturnThis();
}

class MockAudioContext {
	currentTime = 0;
	state = 'running';
	createOscillator = vi.fn(() => new MockOscillator());
	createGain = vi.fn(() => new MockGainNode());
	destination = {};
	resume = vi.fn();
	close = vi.fn();
}

// Inject mock into globalThis before importing
(globalThis as any).AudioContext = MockAudioContext;
(globalThis as any).webkitAudioContext = MockAudioContext;

// Import after mock setup
import { playSuccess, playClick, playNotif, playFail, playLevelUp, playSkibidi } from './sound';

describe('sound', () => {
	it('playSuccess does not throw', () => {
		expect(() => playSuccess()).not.toThrow();
	});

	it('playClick does not throw', () => {
		expect(() => playClick()).not.toThrow();
	});

	it('playNotif does not throw', () => {
		expect(() => playNotif()).not.toThrow();
	});

	it('playFail does not throw', () => {
		expect(() => playFail()).not.toThrow();
	});

	it('playLevelUp does not throw', () => {
		expect(() => playLevelUp()).not.toThrow();
	});

	it('playSkibidi does not throw', () => {
		expect(() => playSkibidi()).not.toThrow();
	});

	it('handles missing AudioContext gracefully', () => {
		const saved = (globalThis as any).AudioContext;
		delete (globalThis as any).AudioContext;
		delete (globalThis as any).webkitAudioContext;
		expect(() => playSuccess()).not.toThrow();
		(globalThis as any).AudioContext = saved;
	});
});
