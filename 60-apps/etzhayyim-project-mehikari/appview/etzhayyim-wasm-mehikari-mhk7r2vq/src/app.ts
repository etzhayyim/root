// mehikari.etzhayyim.com — L3 edge dispatcher for 監視カメラ search + B2G sales.
//
// PER ADR-2605111200: this Worker holds NO database connection, NO face data,
// NO LLM/inference SDK. All work is dispatched to bpmn-dispatcher →
// LangGraph Server (Granian L3) → murakumo on-prem inference pod (JP-domestic).
//
// HARD CONSTRAINTS (enforced before dispatch):
//   - queryPerson: legalBasis.warrantRef OR legalBasis.enquiryRef MUST be non-empty
//   - registerProspect: optInSource MUST be in {exhibition_list, lecture_host, referral, inbound}
//   - sendSalesEmail: 09:00-17:00 JST weekdays only (else queue), reviewSalesEmail.approved required
//   - exportEvidence: requires sectionChiefDid in addition to supervisorDid (two-stage approval)

import {
	asAgentTool,
	createWorkerExport,
	nsid,
	parseLexiconInput,
	requireApproval,
	withCapabilityTags,
	DecisionClass,
	type LexiconOutput,
} from "@etzhayyim/kotodama-host-sdk";

const ALLOWED_OPT_IN_SOURCES = new Set(["exhibition_list", "lecture_host", "referral", "inbound"]);
const ALLOWED_BUSINESS_DAYS = new Set(["Mon", "Tue", "Wed", "Thu", "Fri"]);

function nowJst(): { day: string; hour: number; minute: number } {
	const fmt = new Intl.DateTimeFormat("en-US", {
		timeZone: "Asia/Tokyo",
		weekday: "short",
		hour: "2-digit",
		minute: "2-digit",
		hour12: false,
	});
	const parts = fmt.formatToParts(new Date());
	const day = parts.find((p) => p.type === "weekday")?.value ?? "Mon";
	const hour = Number(parts.find((p) => p.type === "hour")?.value ?? "0");
	const minute = Number(parts.find((p) => p.type === "minute")?.value ?? "0");
	return { day, hour, minute };
}

function withinBusinessHours(): boolean {
	const { day, hour } = nowJst();
	if (!ALLOWED_BUSINESS_DAYS.has(day)) return false;
	return hour >= 9 && hour < 17;
}

async function dispatchToBpmn(env: Record<string, unknown>, nsidStr: string, input: unknown): Promise<unknown> {
	const url = String(env.BPMN_DISPATCHER_URL ?? "");
	if (!url) throw new Error("BPMN_DISPATCHER_URL not configured");
	const token = String(env.SS_BPMN_DISPATCHER_TOKEN ?? "");
	const res = await fetch(`${url}/dispatch/${encodeURIComponent(nsidStr)}`, {
		method: "POST",
		headers: {
			"content-type": "application/json",
			"authorization": `Bearer ${token}`,
		},
		body: JSON.stringify(input),
	});
	if (!res.ok) throw new Error(`bpmn-dispatcher ${res.status}: ${await res.text()}`);
	return await res.json();
}

export default createWorkerExport((sdk) => {
	// ──────────────────────────────────────────────────────────
	// 検索系 (police operator surface)
	// ──────────────────────────────────────────────────────────
	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.registerCamera"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.registerCamera", body);
			if (!input.agreementId) {
				return JSON.stringify({ status: "rejected", rejectionReason: "agreementId required" });
			}
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.registerCamera", input);
			return JSON.stringify(result);
		},
		asAgentTool("Register a surveillance camera + owner recording-utilisation agreement."),
		withCapabilityTags("camera", "ingestion", "agreement-gated"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.ingestClip"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.ingestClip", body);
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.ingestClip", input);
			return JSON.stringify(result);
		},
		asAgentTool("Ingest a recorded clip; audio track is hard-rejected at decode layer."),
		withCapabilityTags("ingestion", "scene-index"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.queryScene"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.queryScene", body);
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.queryScene", input);
			return JSON.stringify(result);
		},
		asAgentTool("Open-vocabulary Japanese scene search across permitted cameras. No person identification."),
		withCapabilityTags("search", "scene", "non-warrant"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.queryPerson"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.queryPerson", body);
			const lb = (input as { legalBasis?: { warrantRef?: string; enquiryRef?: string } }).legalBasis ?? {};
			if (!(lb.warrantRef && lb.warrantRef.length > 0) && !(lb.enquiryRef && lb.enquiryRef.length > 0)) {
				return JSON.stringify({
					status: "denied",
					error: "WARRANT_OR_ENQUIRY_REQUIRED: queryPerson is hard-gated; provide legalBasis.warrantRef OR legalBasis.enquiryRef.",
				});
			}
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.queryPerson", input);
			return JSON.stringify(result);
		},
		asAgentTool("Person re-identification from a reference photo. Hard-gated by warrant or 捜査関係事項照会書."),
		withCapabilityTags("search", "person", "warrant-gated", "high-pii"),
		requireApproval(DecisionClass.B, 1, "high"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.reviewMatches"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.reviewMatches", body);
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.reviewMatches", input);
			return JSON.stringify(result);
		},
		asAgentTool("Record investigator's human assessment of top-K matches (human_review_gate)."),
		withCapabilityTags("review", "human-in-the-loop"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.exportEvidence"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.exportEvidence", body);
			const i = input as { sectionChiefDid?: string; supervisorDid?: string };
			if (!i.supervisorDid || !i.sectionChiefDid) {
				return JSON.stringify({ error: "TWO_STAGE_APPROVAL_REQUIRED: supervisorDid + sectionChiefDid both required." });
			}
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.exportEvidence", input);
			return JSON.stringify(result);
		},
		asAgentTool("Generate JP police evidence packet (監視カメラ捜査報告書 / 証拠資料目録 / 送致書 / chain_of_custody)."),
		withCapabilityTags("export", "evidence", "chain-of-custody"),
		requireApproval(DecisionClass.B, 2, "high"),
	);

	// ──────────────────────────────────────────────────────────
	// 営業系 (internal sales surface)
	// ──────────────────────────────────────────────────────────
	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.registerProspect"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.registerProspect", body);
			const i = input as { optInSource?: string; optInAt?: string };
			if (!i.optInSource || !ALLOWED_OPT_IN_SOURCES.has(i.optInSource)) {
				return JSON.stringify({ status: "rejectedOptInSource", error: `optInSource must be one of ${[...ALLOWED_OPT_IN_SOURCES].join(", ")}` });
			}
			if (!i.optInAt) {
				return JSON.stringify({ status: "rejectedOptInMissing", error: "optInAt required" });
			}
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.registerProspect", input);
			return JSON.stringify(result);
		},
		asAgentTool("Register an outbound sales prospect with mandatory opt-in evidence."),
		withCapabilityTags("sales", "opt-in-gated"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.draftSalesEmail"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.draftSalesEmail", body);
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.draftSalesEmail", input);
			return JSON.stringify(result);
		},
		asAgentTool("Draft an outbound sales email (LangGraph: enrich → draft → safety_review)."),
		withCapabilityTags("sales", "draft", "safety-reviewed"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.reviewSalesEmail"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.reviewSalesEmail", body);
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.reviewSalesEmail", input);
			return JSON.stringify(result);
		},
		asAgentTool("Sales-manager approval gate for a generated draft (kaisya consent helper)."),
		withCapabilityTags("sales", "approval-gated"),
		requireApproval(DecisionClass.C, 1, "low"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.sendSalesEmail"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.sendSalesEmail", body);
			const i = input as { scheduleHint?: string };
			if (i.scheduleHint !== "nextBusinessHour" && !withinBusinessHours()) {
				return JSON.stringify({ status: "rejectedOutsideHours", error: "Outside 09:00-17:00 JST weekdays; resubmit with scheduleHint=nextBusinessHour to queue." });
			}
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.sendSalesEmail", input);
			return JSON.stringify(result);
		},
		asAgentTool("Dispatch an approved draft via microsoft.etzhayyim.com. Idempotent on draftId."),
		withCapabilityTags("sales", "send", "business-hours-gated"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.handleInboundReply"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.handleInboundReply", body);
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.handleInboundReply", input);
			return JSON.stringify(result);
		},
		asAgentTool("Process inbound reply (Cloudflare email worker → reply.mehikari.etzhayyim.com)."),
		withCapabilityTags("sales", "inbound"),
	);

	sdk.app.command(
		nsid("com.etzhayyim.apps.mehikari.unsubscribe"),
		async (_ctx, body) => {
			const input = parseLexiconInput("com.etzhayyim.apps.mehikari.unsubscribe", body);
			const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.unsubscribe", input);
			return JSON.stringify(result);
		},
		asAgentTool("Honour opt-out request (特電法 §3 mandatory + hard delete per root rule)."),
		withCapabilityTags("sales", "opt-out", "hard-delete"),
	);

	// ──────────────────────────────────────────────────────────
	// Queries
	// ──────────────────────────────────────────────────────────
	sdk.app.query(nsid("com.etzhayyim.apps.mehikari.listQueries"), async (_ctx, body) => {
		const input = parseLexiconInput("com.etzhayyim.apps.mehikari.listQueries", body);
		const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.listQueries", input);
		return JSON.stringify(result);
	});

	sdk.app.query(nsid("com.etzhayyim.apps.mehikari.getAuditTrail"), async (_ctx, body) => {
		const input = parseLexiconInput("com.etzhayyim.apps.mehikari.getAuditTrail", body);
		const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.getAuditTrail", input);
		return JSON.stringify(result);
	});

	sdk.app.query(nsid("com.etzhayyim.apps.mehikari.listOutreach"), async (_ctx, body) => {
		const input = parseLexiconInput("com.etzhayyim.apps.mehikari.listOutreach", body);
		const result = await dispatchToBpmn(sdk.env, "com.etzhayyim.apps.mehikari.listOutreach", input);
		return JSON.stringify(result);
	});

	// ──────────────────────────────────────────────────────────
	// /embed for appview integration
	// ──────────────────────────────────────────────────────────
	sdk.router.get("/embed", (ctx) => {
		return new Response(
			`<!doctype html><html><head><meta charset="utf-8"><title>mehikari embed</title></head><body><script>window.parent?.postMessage({type:'etzhayyim:embed:ready',nanoid:'mhk7r2vq'},'*')</script></body></html>`,
			{ headers: { "content-type": "text/html; charset=utf-8" } },
		);
	});
});
