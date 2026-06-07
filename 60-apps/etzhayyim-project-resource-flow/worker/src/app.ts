// resource-flow.etzhayyim.com thin XRPC facade. Domain reads/writes run in AgentGateway MCP + pod-side LangServer.

import {
  asAgentTool,
  createWorkerExport,
  withCapabilityTags,
  type HostSDK,
  nowISO,
  str,
} from "@etzhayyim/kotodama-host-sdk";

interface Env {
  DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string | { get(): Promise<string> };
  PRIMARY_DID?: string;
  SS_ORG_ID?: string;
  SS_USER_ID?: string;
  SS_USER_DID?: string;
}

interface CommitEvent {
  collection: string;
  uri: string;
  cid?: string;
  action: string;
  record?: unknown;
  observedAt?: string;
}

const PRIMARY_DID = "did:web:resource-flow.etzhayyim.com";

function paramsFromBody(raw: unknown): Record<string, unknown> {
  if (!raw) return {};
  if (raw instanceof Uint8Array) {
    try {
      const parsed = JSON.parse(new TextDecoder().decode(raw));
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    } catch {
      return {};
    }
  }
  return raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> : {};
}

function ctx(sdk: HostSDK): { primaryDid: string; orgId: string; userId: string; reviewerDid: string } {
  const env = sdk.env as unknown as Env;
  const primaryDid = env.PRIMARY_DID || PRIMARY_DID;
  return {
    primaryDid,
    orgId: env.SS_ORG_ID || "anon",
    userId: env.SS_USER_ID || "anon",
    reviewerDid: env.SS_USER_DID || primaryDid,
  };
}

async function internalTrustSecret(env: Env): Promise<string> {
  const binding = env.DISPATCHER_INTERNAL_SECRET;
  if (!binding) return "";
  try {
    return typeof binding === "string" ? binding : await binding.get();
  } catch {
    return "";
  }
}

async function dispatchBpmn(sdk: HostSDK, nsid: string, body: unknown): Promise<unknown> {
  const env = sdk.env as unknown as Env;
  const base = (env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const headers: Record<string, string> = { "content-type": "application/json" };
  const trust = await internalTrustSecret(env);
  if (trust) headers["x-internal-trust"] = trust;

  const defaults = ctx(sdk);
  const payload = { ...defaults, ...paramsFromBody(body) };
  const resp = await fetch(`${base}/xrpc/${nsid}`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const text = await resp.text();
  try {
    const parsed = text ? JSON.parse(text) : {};
    return resp.ok ? parsed : { error: "DispatcherError", status: resp.status, body: parsed };
  } catch {
    return resp.ok ? { ok: true, text } : { error: "DispatcherError", status: resp.status, message: text };
  }
}

async function handleCommit(sdk: HostSDK, commit: CommitEvent): Promise<void> {
  if (!commit || commit.action !== "create") return;
  const c = commit.collection;
  let flowClass = "";
  if (c === "com.etzhayyim.apps.resourceFlow.legalEntityCurrencyFlow") flowClass = "currency";
  else if (c === "com.etzhayyim.apps.resourceFlow.legalEntityServiceFlow") flowClass = "service";
  else if (c === "com.etzhayyim.apps.resourceFlow.legalEntityPersonnelFlow") flowClass = "personnel";
  else return;

  await dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.projectFlow", {
    flowClass,
    recordUri: commit.uri,
    observedAt: commit.observedAt ?? nowISO(),
    record: commit.record ?? {},
  });
}

export default createWorkerExport((sdk: HostSDK) => {
  sdk.app.query("com.etzhayyim.apps.resourceFlow.getSankey", async (_ctx, body) => {
    return dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.getSankey", body);
  }, {
    agentTool: "Return the sankey-ready edge list for one flow class.",
    capabilityTags: ["resource-flow", "sankey", "adr-0028"],
  });

  sdk.app.query("com.etzhayyim.apps.resourceFlow.getActorLabels", async (_ctx, body) => {
    return dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.getActorLabels", body);
  }, {
    agentTool: "Bulk-resolve display labels for actor DIDs.",
    capabilityTags: ["resource-flow", "actor-label", "adr-0074"],
  });

  sdk.app.query("com.etzhayyim.apps.resourceFlow.listFlows", async (_ctx, body) => {
    return dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.listFlows", body);
  });

  sdk.app.query("com.etzhayyim.apps.resourceFlow.listAnomalies", async (_ctx, body) => {
    return dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.listAnomalies", body);
  }, {
    agentTool: "Paginated list of resource-flow anomalies.",
    capabilityTags: ["resource-flow", "anomaly", "list", "adr-0046"],
  });

  sdk.app.command("com.etzhayyim.apps.resourceFlow.reviewAnomaly", async (body) => {
    return dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.reviewAnomaly", body);
  }, {
    agentTool: "Record a review action on an anomaly.",
    capabilityTags: ["resource-flow", "anomaly", "review", "adr-0046"],
  });

  sdk.app.command("com.etzhayyim.apps.resourceFlow.projectFlow", async (body) => {
    return dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.projectFlow", body);
  });

  sdk.app.command("com.etzhayyim.apps.resourceFlow.detectAnomaly", async (body) => {
    return dispatchBpmn(sdk, "com.etzhayyim.apps.resourceFlow.detectAnomaly", body);
  }, {
    agentTool: "Run the resource-flow anomaly scan through BPMN/LangServer.",
    capabilityTags: ["resource-flow", "anomaly", "adr-0028", "adr-0046"],
  });

  sdk.app.onCommit?.(async (commit: CommitEvent) => {
    try {
      await handleCommit(sdk, commit);
    } catch (err) {
      console.error("resource-flow.onCommit dispatch failed", str(err));
    }
  });
}, { mcpRegistry: {} });
