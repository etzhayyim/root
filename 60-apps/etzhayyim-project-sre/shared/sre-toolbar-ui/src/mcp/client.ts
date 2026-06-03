export type McpCallResult<T = unknown> = {
  result: T;
  isError?: boolean;
  error?: string;
};

export async function callMcpTool<T = unknown>(params: {
  endpoint: string;
  toolName: string;
  arguments: Record<string, unknown>;
  authToken?: string;
}): Promise<T> {
