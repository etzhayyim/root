import { test as base, createBdd } from 'playwright-bdd';

const BASE_URL = process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com';
const API_BASE = `${BASE_URL}/xrpc`;

interface ApiState {
	lastResponse: Response | null;
	lastBody: Record<string, unknown> | null;
	lastResponseTime: number;
	createdConvoId: string;
	lastMessageRkey: string;
	lastMessageId: string;
	rootMessageRkey: string;
	rootMessageId: string;
}

export const test = base.extend<{ apiState: ApiState; apiBase: string; baseUrl: string }>({
	apiState: async ({}, use) => {
		await use({
			lastResponse: null,
			lastBody: null,
			lastResponseTime: 0,
			createdConvoId: '',
			lastMessageRkey: '',
			lastMessageId: '',
			rootMessageRkey: '',
			rootMessageId: '',
		});
	},
	apiBase: async ({}, use) => {
		await use(API_BASE);
	},
	baseUrl: async ({}, use) => {
		await use(BASE_URL);
	},
});

export const { Given, When, Then } = createBdd(test);
