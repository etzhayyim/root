import { writable } from 'svelte/store';
import type { McpResponse } from './types.js';

export const mcpConnected = writable<boolean>(false);
export const mcpLoading = writable<boolean>(false);
export const mcpLastError = writable<McpResponse | null>(null);
