const BASE = typeof window !== "undefined" ? window.location.origin : "https://mamoru.etzhayyim.com";
const KEY_STORAGE = "mamoru_api_key";

export function getApiKey(): string {
  return typeof localStorage !== "undefined" ? (localStorage.getItem(KEY_STORAGE) ?? "") : "";
}

export function setApiKey(key: string): void {
  if (typeof localStorage !== "undefined") localStorage.setItem(KEY_STORAGE, key);
}

async function xrpcGet<T>(nsid: string, params: Record<string, string | number | undefined> = {}): Promise<T> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) q.set(k, String(v));
  }
  const url = `${BASE}/xrpc/${nsid}${q.toString() ? "?" + q : ""}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${getApiKey()}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error((err.error as string) ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function xrpcPost<T>(nsid: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}/xrpc/${nsid}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getApiKey()}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error((err.error as string) ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export type SeverityLabel = "critical" | "high" | "medium" | "low" | "info";
export type IncidentStatus = "open" | "resolved" | "false_positive" | "accepted_risk";
export type ValidityStatus = "valid" | "invalid" | "unknown";

export interface IncidentSummary {
  incidentId: string;
  repoId: string;
  secretType: string;
  severityPermille: number;
  status: IncidentStatus;
  validity: ValidityStatus;
  firstSeenAt: string;
  lastSeenAt: string;
  occurrenceCount: number;
  commitCount: number;
}

export interface Occurrence {
  occurrenceId: string;
  commitSha: string;
  filePath: string;
  lineNumber?: number;
  secretHash: string;
  detectedAt: string;
}

export interface IncidentDetail extends IncidentSummary {
  occurrences: Occurrence[];
}

export interface ListIncidentsResponse {
  incidents: IncidentSummary[];
  total: number;
  offset: number;
  limit: number;
}

export function severityLabel(permille: number): SeverityLabel {
  if (permille >= 900) return "critical";
  if (permille >= 700) return "high";
  if (permille >= 400) return "medium";
  if (permille >= 100) return "low";
  return "info";
}

export function severityPercent(permille: number): string {
  return (permille / 10).toFixed(0) + "%";
}

export const api = {
  listIncidents(params: {
    repoId?: string;
    status?: IncidentStatus;
    severityMinPermille?: number;
    validity?: ValidityStatus;
    limit?: number;
    offset?: number;
  } = {}): Promise<ListIncidentsResponse> {
    return xrpcGet("com.etzhayyim.apps.mamoru.listIncidents", params as Record<string, string | number | undefined>);
  },

  getIncident(incidentId: string, occurrenceLimit = 20): Promise<IncidentDetail> {
    return xrpcGet("com.etzhayyim.apps.mamoru.getIncident", { incidentId, occurrenceLimit });
  },

  resolveIncident(incidentId: string, resolution: "revoked" | "false_positive" | "accepted_risk", note?: string): Promise<{ ok: boolean }> {
    return xrpcPost("com.etzhayyim.apps.mamoru.resolveIncident", { incidentId, resolution, note });
  },

  scanCommit(repoId: string, commitSha: string, diffPayload = ""): Promise<{ scanId: string }> {
    return xrpcPost("com.etzhayyim.apps.mamoru.scanCommit", {
      repoId,
      commitSha,
      diffPayload: btoa(diffPayload),
    });
  },
};
