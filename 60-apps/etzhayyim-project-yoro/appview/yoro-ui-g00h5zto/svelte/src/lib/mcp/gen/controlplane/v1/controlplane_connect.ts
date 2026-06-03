// v2-compatible replacement for protoc-gen-connect-es v1 output.
// Uses Struct-based I/O for Connect v2 createClient compatibility.

import { StructSchema } from '@bufbuild/protobuf/wkt';
import { MethodOptions_IdempotencyLevel } from '@bufbuild/protobuf/wkt';
import type { DescService } from '@bufbuild/protobuf';

function createStructService(
	typeName: string,
	methods: ReadonlyArray<{ localName: string; name: string; streaming?: boolean }>,
): DescService {
	const service = {
		kind: 'service',
		typeName,
		methods: [] as Array<Record<string, unknown>>,
	} as unknown as DescService;

	const builtMethods = methods.map(({ localName, name, streaming }) => ({
		kind: 'rpc',
		name,
		localName,
		methodKind: streaming ? 'server_streaming' : 'unary',
		input: StructSchema,
		output: StructSchema,
		idempotency: MethodOptions_IdempotencyLevel.IDEMPOTENCY_UNKNOWN,
		parent: service,
	}));
	(service as unknown as { methods: Array<Record<string, unknown>> }).methods = builtMethods;
	return service;
}

/**
 * ControlPlaneService is the central API for etzhayyim CLI.
 * All operations require Clerk JWT authentication.
 * Resources are scoped by org_id extracted from the JWT.
 */
export const ControlPlaneService = createStructService(
	'controlplane.v1.ControlPlaneService',
	[
		{ localName: 'whoAmI', name: 'WhoAmI' },
		{ localName: 'deploy', name: 'Deploy' },
		{ localName: 'beginStaticDeploy', name: 'BeginStaticDeploy' },
		{ localName: 'finalizeStaticDeploy', name: 'FinalizeStaticDeploy' },
		{ localName: 'upsertStaticProxyMapping', name: 'UpsertStaticProxyMapping' },
		{ localName: 'getDeploymentStatus', name: 'GetDeploymentStatus' },
		{ localName: 'listDeployments', name: 'ListDeployments' },
		{ localName: 'deleteDeployment', name: 'DeleteDeployment' },
		{ localName: 'restartDeployment', name: 'RestartDeployment' },
		{ localName: 'scaleDeployment', name: 'ScaleDeployment' },
		{ localName: 'listDNSDomains', name: 'ListDNSDomains' },
		{ localName: 'listDNSRecords', name: 'ListDNSRecords' },
		{ localName: 'upsertDNSRecord', name: 'UpsertDNSRecord' },
		{ localName: 'deleteDNSRecord', name: 'DeleteDNSRecord' },
		{ localName: 'listDaprShared', name: 'ListDaprShared' },
		{ localName: 'ensureDaprShared', name: 'EnsureDaprShared' },
		{ localName: 'streamLogs', name: 'StreamLogs', streaming: true },
	],
);

/**
 * MCPService exposes control plane as MCP tools for AI agents.
 */
export const MCPService = createStructService(
	'controlplane.v1.MCPService',
	[
		{ localName: 'getInfo', name: 'GetInfo' },
		{ localName: 'listTools', name: 'ListTools' },
		{ localName: 'callTool', name: 'CallTool' },
	],
);
