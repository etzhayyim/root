import { AtpAgent } from '@etzhayyim/sdk/atproto';
import type { McpResponse, McpClientConfig } from './types.js';

function toText(value: unknown): string {
	if (typeof value === 'string') return value;
	try {
		return JSON.stringify(value) ?? String(value);
	} catch {
		return String(value);
	}
}

export class McpClient {
	private toolEndpoints: Record<string, string>;
	private defaultEndpoint: string | null;
	private mcpServicePath: string;
	private getAuthToken: () => Promise<string | null>;
	private getOrgId: () => Promise<string | null>;
	private getUserId: () => Promise<string | null>;
	private requireOrgContext: boolean;

	constructor(config: McpClientConfig = {}) {
		this.toolEndpoints = config.toolEndpoints ?? {};
		this.defaultEndpoint = config.defaultEndpoint ?? null;
		this.mcpServicePath = (config.mcpServicePath ?? 'controlplane.v1.MCPService').replace(/^\/+/, '');
		this.getAuthToken = config.getAuthToken ?? (async () => null);
		this.getOrgId = async () => {
			const orgId = config.getOrgId ? await config.getOrgId() : null;
			return orgId?.trim() ? orgId : null;
		};
		this.getUserId = async () => {
			const userId = config.getUserId ? await config.getUserId() : null;
			return userId?.trim() ? userId : null;
		};
		this.requireOrgContext = !!config.requireOrgContext;
	}

	registerEndpoint(toolName: string, endpoint: string): void {
		this.toolEndpoints[toolName] = endpoint;
	}

	registerEndpoints(endpoints: Record<string, string>): void {
		Object.assign(this.toolEndpoints, endpoints);
	}

	private errorResponse(message: string): McpResponse {
		return {
			content: [{ type: 'text', text: message }],
			'isError': true,
		};
	}

	private async getHeaders(): Promise<Record<string, string>> {
		const headers: Record<string, string> = {};
		const orgId = await this.getOrgId();
		if (orgId) {
			headers['X-etzhayyim-ORG-ID'] = orgId;
		} else if (this.requireOrgContext) {
			throw new Error('missing org context (orgId)');
		}
		const userId = await this.getUserId();
		if (userId) {
			headers['X-etzhayyim-USER-ID'] = userId;
		}
		return headers;
	}

	private resolveBaseUrl(endpoint: string): string {
		const trimmed = endpoint.replace(/\/+$/, '');
		if (trimmed === '/api/mcp') return trimmed;
		const normalized = trimmed.replace(/\/api\/mcp(?=\/|$)/, '/xrpc');
		const escapedPath = this.mcpServicePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
		return normalized
			.replace(new RegExp(`/${escapedPath}(?:/(?:ListTools|CallTool))?$`), '')
			.replace(/\/(?:ListTools|CallTool)$/, '');
	}

	private createAgent(endpoint: string): AtpAgent {
		const baseUrl = this.resolveBaseUrl(endpoint);
		return new AtpAgent({ service: baseUrl || 'https://atproto.etzhayyim.com' });
	}

	private async buildHeaders(extraHeaders?: Record<string, string>): Promise<Record<string, string>> {
		const inherited = await this.getHeaders();
		const headers: Record<string, string> = { 'content-type': 'application/json', ...inherited, ...(extraHeaders ?? {}) };
		const token = await this.getAuthToken();
		if (token) headers.authorization = `Bearer ${token}`;
		return headers;
	}

	private async connectPost<T>(
		agent: AtpAgent,
		headers: Record<string, string>,
		method: string,
		body: Record<string, unknown> = {}
	): Promise<T> {
		const res = await agent.api.call('com.etzhayyim.apps.yoro.' + method, body, undefined, { headers });
		return res.data as T;
	}

	private async jsonRpcPost<T>(
		endpoint: string,
		headers: Record<string, string>,
		method: string,
		params: Record<string, unknown> = {}
	): Promise<T> {
		const res = await fetch(endpoint, {
			method: 'POST',
			headers,
			body: JSON.stringify({ jsonrpc: '2.0', id: Date.now(), method, params }),
		});
		const data = await res.json() as { result?: T; error?: { message?: string } };
		if (!res.ok || data.error) throw new Error(data.error?.message ?? `MCP HTTP ${res.status}`);
		return data.result as T;
	}

	async listTools(endpoint?: string, extraHeaders?: Record<string, string>): Promise<McpResponse> {
		const target = endpoint ?? this.defaultEndpoint;
		if (!target) return this.errorResponse('No MCP endpoint configured for listTools()');
		try {
			const headers = await this.buildHeaders(extraHeaders);
			const res = target.startsWith('/api/mcp')
				? await this.jsonRpcPost<Record<string, unknown>>(target, headers, 'tools/list', {})
				: await this.connectPost<Record<string, unknown>>(this.createAgent(target), headers, 'listTools', {});
			return {
				content: [{ type: 'text', text: toText(res) }],
				'isError': false,
			};
		} catch (error) {
			console.error('MCP ListTools failed', error);
			return this.errorResponse(`ListTools failed: ${error instanceof Error ? error.message : String(error)}`);
		}
	}

	async callTool(
		name: string,
		args: Record<string, unknown> = {},
		endpoint?: string,
		extraHeaders?: Record<string, string>
	): Promise<McpResponse> {
		const targetEndpoint = endpoint ?? this.toolEndpoints[name] ?? this.defaultEndpoint;
		if (!targetEndpoint) {
			return this.errorResponse(`No endpoint configured for tool "${name}"`);
		}
		try {
			const headers = await this.buildHeaders(extraHeaders);
			const res = targetEndpoint.startsWith('/api/mcp')
				? await this.jsonRpcPost<Record<string, unknown>>(targetEndpoint, headers, 'tools/call', { name, arguments: args })
				: await this.connectPost<Record<string, unknown>>(this.createAgent(targetEndpoint), headers, 'callTool', { name, arguments: JSON.stringify(args) });
			return {
				content: [{ type: 'text', text: (res.content as string) || '{}' }],
				'isError': !!(res.isError ?? res.isError),
			};
		} catch (error) {
			console.error('MCP CallTool failed', error);
			return this.errorResponse(`CallTool failed: ${error instanceof Error ? error.message : String(error)}`);
		}
	}

	parseResponse<T = Record<string, unknown>>(response: McpResponse): T | null {
		if (response.isError) return null;
		try {
			return JSON.parse(response.content[0]?.text || '{}');
		} catch {
			return null;
		}
	}
}
