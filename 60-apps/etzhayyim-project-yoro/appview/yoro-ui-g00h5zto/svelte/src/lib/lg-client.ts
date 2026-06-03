import { Client } from '@langchain/langgraph-sdk';

export function createLangGraphClient(): Client {
	return new Client({ apiUrl: '/api/pregel' });
}
