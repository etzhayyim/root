// outbox-forward.ts — admin-gated XRPC shim from yatabase Worker to
// lg-yatabase pod for vertex_email_outbox review actions (P21).
//
// The yatabase Worker already enforces x-yata-admin-key on the caller
// side; this module forwards trusted requests to the pod using the
// same HMAC-trust contract used by leads-forward.ts / auth-forward.ts.
//
// Per ADR-2605111200 the Worker never touches Hyperdrive — vertex_
// email_outbox writes (approve/reject) all flow through the pod.

import { forwardBmc, type ForwardEnv, type ForwardIdentity, type ForwardResult } from "./bmc-forward";

const SYSTEM_IDENTITY: ForwardIdentity = {
	did: "agent:yatabase-worker",
	orgDid: "agent:yatabase-worker",
};

function withTrace(traceId?: string): ForwardIdentity {
	return traceId ? { ...SYSTEM_IDENTITY, traceId } : SYSTEM_IDENTITY;
}

export interface OutboxListInput {
	status?: string;
	kind?: string;
	limit?: number;
}

export async function forwardOutboxList(
	env: ForwardEnv,
	body: OutboxListInput,
	traceId?: string,
): Promise<ForwardResult> {
	return forwardBmc(
		env,
		"POST",
		"com.etzhayyim.apps.yata.outboxList",
		body as Record<string, unknown>,
		withTrace(traceId),
		{ timeoutMs: 10_000 },
	);
}

export interface OutboxApproveInput {
	vertex_id: string;
	recipient_email: string;
	recipient_name?: string;
	body_text?: string;
	body_html?: string;
	subject?: string;
}

export async function forwardOutboxApprove(
	env: ForwardEnv,
	body: OutboxApproveInput,
	traceId?: string,
): Promise<ForwardResult> {
	return forwardBmc(
		env,
		"POST",
		"com.etzhayyim.apps.yata.outboxApprove",
		body as Record<string, unknown>,
		withTrace(traceId),
		{ timeoutMs: 10_000 },
	);
}

export interface OutboxRejectInput {
	vertex_id: string;
	reason?: string;
}

export async function forwardOutboxReject(
	env: ForwardEnv,
	body: OutboxRejectInput,
	traceId?: string,
): Promise<ForwardResult> {
	return forwardBmc(
		env,
		"POST",
		"com.etzhayyim.apps.yata.outboxReject",
		body as Record<string, unknown>,
		withTrace(traceId),
		{ timeoutMs: 10_000 },
	);
}
