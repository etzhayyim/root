export interface McpResponse {
	content: { type: string; text: string }[];
	'isError': boolean;
	model?: string;
	provider?: string;
}

export interface McpClientConfig {
	/** Map of tool name to MCP endpoint URL. */
	toolEndpoints?: Record<string, string>;
	/** Default MCP endpoint for tools not in the map. */
	defaultEndpoint?: string;
	/** MCP service path for Connect-RPC method suffix (default: controlplane.v1.MCPService). */
	mcpServicePath?: string;
	/** Function to retrieve auth token for API requests. */
	getAuthToken?: () => Promise<string | null>;
	/** Function to retrieve org context for org-aware MCP endpoints. */
	getOrgId?: () => Promise<string | null> | string | null;
	/** Function to retrieve user context for user-aware MCP endpoints. */
	getUserId?: () => Promise<string | null> | string | null;
	/** If true, fail requests when org context is missing. */
	requireOrgContext?: boolean;
}
