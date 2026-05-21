// well-known.ts — `/.well-known/{agent,mcp}.json` discovery documents.
//
// Public, no auth. Static metadata that AI agents and a2a / MCP discovery
// crawlers fetch to learn how to talk to yatabase.

import { listMcpTools } from "./mcp";

export interface WellKnownEnv {
  YATA_VERSION?: string;
  YATA_ACTOR_DID?: string;
}

export function buildAgentJson(env: WellKnownEnv): Record<string, unknown> {
  return {
    name: "yatabase",
    description:
      "Yatabase — graph database BaaS with integrated S3-compat storage, SPARQL, openCypher, and streaming MV. Cell-membrane MCP facade per ADR-2605091400.",
    url: "https://yatabase.gftd.ai",
    provider: {
      organization: "etz hayim",
      vendor: "Gftd Japan株式会社",
      url: "https://gftd.group",
    },
    version: env.YATA_VERSION ?? "0.0.0",
    did: env.YATA_ACTOR_DID ?? "did:web:yatabase.gftd.ai",
    documentationUrl: "https://yatabase.gftd.ai/_app/meta",
    capabilities: {
      streaming: false,
      pushNotifications: false,
      stateTransitionHistory: false,
      authentication: { schemes: ["bearer", "atproto-oauth"] },
    },
    skills: listMcpTools().map((t) => ({
      id: t.name,
      name: t.name,
      description: `XRPC NSID: ${t.nsid}`,
    })),
    defaultInputModes: ["application/json"],
    defaultOutputModes: ["application/json", "text/plain"],
  };
}

export function buildMcpJson(env: WellKnownEnv): Record<string, unknown> {
  return {
    name: "yatabase",
    description: "MCP server for yatabase graph + storage (cell-membrane facade).",
    version: env.YATA_VERSION ?? "0.0.0",
    protocolVersion: "2025-06-18",
    transport: "streamable-http",
    endpoint: "https://yatabase.gftd.ai/mcp",
    auth: {
      schemes: ["bearer", "atproto-oauth"],
      publicMethods: [
        "initialize",
        "ping",
        "tools/list",
        "resources/list",
        "prompts/list",
      ],
      authenticatedMethods: ["tools/call", "resources/read", "prompts/get"],
    },
    capabilities: {
      tools: { listChanged: false },
      resources: { subscribe: false, listChanged: false },
      prompts: { listChanged: false },
    },
    tools: listMcpTools().map((t) => ({ name: t.name, nsid: t.nsid })),
    documentation: {
      adr: "https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080000-yatabase-yata-retail-cloud.md",
      meta: "https://yatabase.gftd.ai/_app/meta",
    },
  };
}
