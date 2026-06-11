#!/usr/bin/env node
import readline from "node:readline";
import {
  buildSqlUpsertPayload,
  parseJsonFile,
  tryCueVet,
  validateCloudflarePipelines,
} from "./core.mjs";

function getArg(name, fallback = "") {
  const idx = process.argv.indexOf(name);
  if (idx < 0) return fallback;
  return process.argv[idx + 1] ?? fallback;
}

function runLintMode() {
  const configPath = getArg("--config", "rules/compliance/seigen/cloudflare-pipelines.input.example.json");
  const locale = getArg("--locale", "ja");
  const enforceCue = process.env.SEIGEN_ENFORCE_CUE === "1";
  const input = parseJsonFile(configPath, locale);
  const result = validateCloudflarePipelines(input, { locale });
  const cue = tryCueVet(configPath, { locale });
  if (!cue.ok && enforceCue) {
    console.error(JSON.stringify({ ok: false, reason: "cue", cue }, null, 2));
    process.exit(1);
  }
  const output = { ok: result.ok, result, cue };
  console.log(JSON.stringify(output, null, 2));
  process.exit(result.ok ? 0 : 1);
}

function runSqlUpsertMode() {
  const payload = buildSqlUpsertPayload({
    policyId: getArg("--policy-id", "cf.pipelines.limits"),
    version: getArg("--version", "2026-03-27"),
    sourceDate: getArg("--source-date", "2026-03-27"),
    actorDid: getArg("--actor-did", "did:web:seigen.etzhayyim.com"),
    locale: getArg("--locale", "ja"),
  });
  console.log(JSON.stringify(payload, null, 2));
  process.exit(0);
}

function mcpToolsList() {
  return [
    {
      name: "seigen.validate",
      description: "Validate Cloudflare Pipelines config with Seigen policy.",
      inputSchema: {
        type: "object",
        properties: {
          configPath: { type: "string" },
          locale: { type: "string", enum: ["ja", "en"] },
          enforceCue: { type: "boolean" },
        },
        required: ["configPath"],
      },
    },
    {
      name: "seigen.policy.exportSql",
      description: "Build parameterized SQL payload for policy upsert.",
      inputSchema: {
        type: "object",
        properties: {
          policyId: { type: "string" },
          version: { type: "string" },
          sourceDate: { type: "string" },
          actorDid: { type: "string" },
          locale: { type: "string", enum: ["ja", "en"] },
        },
      },
    },
  ];
}

function success(id, result) {
  return { jsonrpc: "2.0", id, result };
}

function failure(id, message) {
  return { jsonrpc: "2.0", id, error: { code: -32000, message } };
}

async function runMcpMode() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false });
  rl.on("line", (line) => {
    const text = line.trim();
    if (!text) return;
    let req;
    try {
      req = JSON.parse(text);
    } catch {
      process.stdout.write(JSON.stringify(failure(null, "Invalid JSON")) + "\n");
      return;
    }

    const id = req?.id ?? null;
    if (req?.method === "tools/list") {
      process.stdout.write(JSON.stringify(success(id, { tools: mcpToolsList() })) + "\n");
      return;
    }

    if (req?.method === "tools/call") {
      const name = req?.params?.name;
      const args = req?.params?.arguments ?? {};
      if (name === "seigen.validate") {
        try {
          const locale = args.locale === "en" ? "en" : "ja";
          const input = parseJsonFile(args.configPath, locale);
          const result = validateCloudflarePipelines(input, { locale });
          const cue = tryCueVet(args.configPath, { locale });
          if (args.enforceCue === true && !cue.ok) {
            process.stdout.write(JSON.stringify(success(id, { ok: false, reason: "cue", cue })) + "\n");
            return;
          }
          process.stdout.write(JSON.stringify(success(id, { ok: result.ok, result, cue })) + "\n");
          return;
        } catch (error) {
          process.stdout.write(JSON.stringify(failure(id, String(error.message || error))) + "\n");
          return;
        }
      }
      if (name === "seigen.policy.exportSql") {
        try {
          const payload = buildSqlUpsertPayload(args);
          process.stdout.write(JSON.stringify(success(id, payload)) + "\n");
          return;
        } catch (error) {
          process.stdout.write(JSON.stringify(failure(id, String(error.message || error))) + "\n");
          return;
        }
      }
      process.stdout.write(JSON.stringify(failure(id, `Unknown tool: ${name}`)) + "\n");
      return;
    }

    if (req?.method === "ping") {
      process.stdout.write(JSON.stringify(success(id, { ok: true })) + "\n");
      return;
    }

    process.stdout.write(JSON.stringify(failure(id, `Unsupported method: ${req?.method || "(none)"}`)) + "\n");
  });
}

function printHelp() {
  console.log(
    [
      "seigen-did-actor",
      "modes:",
      "  lint --config <file> [--locale ja|en]",
      "  sql-upsert [--policy-id <id>] [--version <v>] [--source-date YYYY-MM-DD] [--actor-did <did>] [--locale ja|en]",
      "  mcp",
    ].join("\n"),
  );
}

const mode = process.argv[2] || "help";
if (mode === "lint") {
  runLintMode();
} else if (mode === "sql-upsert") {
  runSqlUpsertMode();
} else if (mode === "mcp") {
  runMcpMode();
} else {
  printHelp();
  process.exit(1);
}
