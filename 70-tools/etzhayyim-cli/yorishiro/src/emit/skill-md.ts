// emit/skill-md.ts — SKILL.md emitter (CLI-Anything format inspired).
//
// SKILL.md is the agent-discoverable summary of what the yorishiro can do.
// Format: YAML frontmatter + Markdown body with tool list and JSON output
// note. Accepts ops from either openapi-v3 (NormalizedOp) or binary-cli
// (BinaryOp) via a structural minimum.

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export interface SkillOp {
  opName: string;
  summary?: string;
  description?: string;
}

export interface EmitSkillArgs {
  repoRoot: string;
  name: string;
  kami: string;
  transport: "openapi-v3" | "binary-cli" | "source-repo" | "browser-only";
  purposes: readonly string[];
  ops: readonly SkillOp[];
}

export function emitSkill(args: EmitSkillArgs): string {
  const dir = join(args.repoRoot, "skills", `etzhayyim-yorishiro-${args.name}`);
  mkdirSync(dir, { recursive: true });
  const out = join(dir, "SKILL.md");
  writeFileSync(out, render(args), "utf-8");
  return out;
}

function render(args: EmitSkillArgs): string {
  const tools = args.ops
    .map((o) => {
      const t = snake(o.opName);
      const summary = (o.summary || o.description || o.opName).replace(/\s+/g, " ").trim();
      return `- \`${t}\` — ${summary}`;
    })
    .join("\n");

  const outputBlock = args.transport === "binary-cli"
    ? `\`\`\`json
{ "exitCode": <number>, "stdout"?: <string>, "stderr"?: <string>, "error"?: <string> }
\`\`\`

\`error\` is set only when the binary could not be launched at all
(missing on PATH, timeout, spawn failure). Otherwise the binary's exit
code, stdout, and stderr are reported verbatim.`
    : `\`\`\`json
{ "httpStatus": <number>, "json"?: <object>, "body"?: <string>, "error"?: <string> }
\`\`\`

\`json\` is present iff the kami returned \`application/json\` and the body
parsed; otherwise the raw response is in \`body\`. \`httpStatus\` is \`0\` if
the kami could not be reached at all.`;

  return `---
name: etzhayyim-yorishiro-${args.name}
description: Drive the ${args.name} yorishiro (kami: ${args.kami}) via MCP tools, XRPC, or in-process kotodama actor calls.
charter_purposes: ${JSON.stringify(args.purposes)}
transport: ${args.transport}
adr: 2605211900
---

# etzhayyim-yorishiro-${args.name}

依代 (vessel) wrapping the **${args.kami}** kami so that agents can drive
it through the etzhayyim substrate. The same op surface is exposed three
ways:

1. **Lexicon** at \`00-contracts/lexicons/ai/etzhayyim/yorishiro/${args.name}/*.json\` (XRPC + kotodama-host-sdk consumers)
2. **Pregel cell** at \`40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_${args.name}/cell.py\` (in-cluster Murakumo runtime)
3. **MCP server** at \`40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-${args.name}-mcp/\` (stdio + Streamable HTTP)

## Tools

${tools}

## JSON output

Every tool returns a JSON object:

${outputBlock}

## Charter purposes

This yorishiro is restricted to: \`${args.purposes.join(", ")}\`. Calls that
would imply a non-listed purpose are rejected at the lexicon validator
seam. See ADR-2605192115 §4.
`;
}

function snake(s: string): string {
  return s.replace(/([a-z0-9])([A-Z])/g, "$1_$2").replace(/[-]/g, "_").toLowerCase();
}
