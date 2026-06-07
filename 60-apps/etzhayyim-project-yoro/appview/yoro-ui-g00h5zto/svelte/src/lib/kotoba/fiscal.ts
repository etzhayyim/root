// Resource-flow reader over the kotoba Datom log (kagami-free).
//
// Replaces the deprecated kagami SQL path (`$lib/graph-sql` →
// `com.etzhayyim.kagami.sql` → RisingWave). The fiscal/ownership edges are read
// as `:yoro.fiscal/*` + `:yoro.ownership/*` datoms from the in-browser kotoba
// Datom log — the first-class canonical state (ADR-2605312345; ADR-2605262130
// forbids Kotoba/Datomic projections).
//
// The query NSID `com.etzhayyim.yoro.fiscal.getResourceFlow` is intercepted by
// kotoba-sw.js (registered in `$lib/atproto-agent` SW_LOCAL_NSIDS so it is sent
// same-origin), which assembles the view entirely in the browser. `asOf` is a
// Datomic-style point-in-time: an ISO date (YYYY-MM-DD); omitted = current head.

import { atQuery } from '$lib/atproto-agent';

export interface FlowRow {
	from_did: string;
	to_did: string;
	stage: string;
	fiscal_year: number | null;
	amount_jpy: number | null;
	basis: string | null;
	program_code: string | null;
	source_url: string | null;
	observed_at: string | null;
}

export interface OwnershipRow {
	parent_did: string;
	child_did: string;
	ownership_pct: number | null;
	voting_pct: number | null;
	evidence_kind: string | null;
	evidence_url: string | null;
	observed_at: string | null;
}

export interface ResourceFlow {
	incoming: FlowRow[];
	outgoing: FlowRow[];
	uboParents: OwnershipRow[];
	uboChildren: OwnershipRow[];
	totalIn: number;
	totalOut: number;
}

const EMPTY: ResourceFlow = {
	incoming: [],
	outgoing: [],
	uboParents: [],
	uboChildren: [],
	totalIn: 0,
	totalOut: 0,
};

/**
 * Read the resource flow for an actor DID from the kotoba Datom log.
 * @param did   the actor DID
 * @param asOf  optional ISO date (YYYY-MM-DD) — show the flow as recorded at or
 *              before that day (as-of fact-time); omit for the current head.
 */
export async function getResourceFlow(did: string, asOf?: string | null): Promise<ResourceFlow> {
	if (!did) return EMPTY;
	const params: Record<string, unknown> = { did };
	if (asOf) params.asOf = asOf;
	const res = await atQuery<Partial<ResourceFlow>>('com.etzhayyim.yoro.fiscal.getResourceFlow', params);
	return {
		incoming: res?.incoming ?? [],
		outgoing: res?.outgoing ?? [],
		uboParents: res?.uboParents ?? [],
		uboChildren: res?.uboChildren ?? [],
		totalIn: res?.totalIn ?? 0,
		totalOut: res?.totalOut ?? 0,
	};
}
