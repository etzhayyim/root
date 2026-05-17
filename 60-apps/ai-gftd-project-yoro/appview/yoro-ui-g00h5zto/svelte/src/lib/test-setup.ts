// Vitest setup: provide a full localStorage mock for all test files
const store: Record<string, string> = {};
const localStorageMock: Storage = {
	length: 0,
	key: (index: number) => Object.keys(store)[index] ?? null,
	getItem: (key: string) => store[key] ?? null,
	setItem: (key: string, val: string) => { store[key] = val; },
	removeItem: (key: string) => { delete store[key]; },
	clear: () => { for (const k in store) delete store[k]; },
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock, writable: true });
