#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { BpmnModdle } from "bpmn-moddle";

const DEFAULT_BPMN_ROOT = "00-contracts/bpmn/com/etzhayyim";
const TASK_RE =
  /<zeebe:taskDefinition\b[^>]*\btype=(["'])(.*?)\1/gu;
const DOC_RE = /<bpmn:documentation\b[^>]*>([\s\S]*?)<\/bpmn:documentation>/u;

function parseArgs(argv) {
  const opts = {
    root: process.cwd(),
    bpmnRoot: DEFAULT_BPMN_ROOT,
    out: "",
    json: false,
    limitFindings: 25,
  };
  for (const arg of argv) {
    if (arg === "--") continue;
    else if (arg === "--json") opts.json = true;
    else if (arg.startsWith("--root=")) opts.root = arg.slice("--root=".length);
    else if (arg.startsWith("--bpmn-root=")) opts.bpmnRoot = arg.slice("--bpmn-root=".length);
    else if (arg.startsWith("--out=")) opts.out = arg.slice("--out=".length);
    else if (arg.startsWith("--limit-findings=")) opts.limitFindings = Number.parseInt(arg.slice("--limit-findings=".length), 10);
    else if (arg === "--help" || arg === "-h") usage(0);
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!Number.isSafeInteger(opts.limitFindings) || opts.limitFindings < 1) {
    throw new Error("--limit-findings must be a positive integer");
  }
  return opts;
}

function usage(code) {
  console.log(`Usage:
  node 70-tools/scripts/process-mining/bpmn-model-mining.mjs [options]

Options:
  --root=DIR          Workspace root. Default: cwd.
  --bpmn-root=DIR     BPMN tree relative to root. Default: ${DEFAULT_BPMN_ROOT}.
  --out=FILE          Write report to FILE. Extension .json writes JSON, otherwise Markdown.
  --json              Print JSON to stdout.
`);
  process.exit(code);
}

async function listFiles(dir) {
  const { readdir } = await import("node:fs/promises");
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await listFiles(abs));
    else if (entry.isFile() && entry.name.endsWith(".bpmn")) files.push(abs);
  }
  return files.sort();
}

function rel(root, abs) {
  return path.relative(root, abs).split(path.sep).join("/");
}

function projectFromPath(relativePath, bpmnRoot) {
  const prefix = `${bpmnRoot.replace(/\/+$/u, "")}/`;
  const withoutRoot = relativePath.startsWith(prefix) ? relativePath.slice(prefix.length) : relativePath;
  return withoutRoot.split("/")[0] || "(root)";
}

function findTaskDefinitionTypes(xml, taskId) {
  const escaped = taskId.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const taskPattern = new RegExp(
    `<bpmn:serviceTask\\b[^>]*\\bid=(["'])${escaped}\\1[\\s\\S]*?</bpmn:serviceTask>`,
    "u",
  );
  const taskMatch = xml.match(taskPattern);
  if (!taskMatch) return [];
  return [...taskMatch[0].matchAll(TASK_RE)].map((match) => match[2].trim()).filter(Boolean);
}

function maybeJsonDocumentation(xml) {
  const match = xml.match(DOC_RE);
  if (!match) return {};
  const text = match[1].replace(/&quot;/gu, "\"").replace(/&gt;/gu, ">").replace(/&lt;/gu, "<").trim();
  if (!text.startsWith("{")) return {};
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

function countBy(items, keyFn) {
  const counts = new Map();
  for (const item of items) {
    const key = keyFn(item);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count || String(a.key).localeCompare(String(b.key)));
}

function percentile(values, q) {
  const nums = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (nums.length === 0) return null;
  return nums[Math.min(nums.length - 1, Math.floor((nums.length - 1) * q))];
}

function taskFamily(type) {
  if (!type) return "missing";
  if (type.startsWith("generic.")) return "generic";
  const first = type.split(".")[0];
  return first || "unknown";
}

function analyzeProcess({ root, bpmnRoot, absPath, rootElement, xml }) {
  const relativePath = rel(root, absPath);
  const processes = (rootElement.rootElements ?? []).filter((element) => element.$type === "bpmn:Process");
  const doc = maybeJsonDocumentation(xml);
  return processes.map((process) => {
    const flowElements = process.flowElements ?? [];
    const serviceTasks = flowElements.filter((element) => element.$type === "bpmn:ServiceTask");
    const startEvents = flowElements.filter((element) => element.$type === "bpmn:StartEvent");
    const endEvents = flowElements.filter((element) => element.$type === "bpmn:EndEvent");
    const gateways = flowElements.filter((element) => String(element.$type).endsWith("Gateway"));
    const sequenceFlows = flowElements.filter((element) => element.$type === "bpmn:SequenceFlow");
    const taskTypes = serviceTasks.flatMap((task) => findTaskDefinitionTypes(xml, task.id));
    const outgoingBySource = new Map();
    for (const flow of sequenceFlows) {
      const sourceId = flow.sourceRef?.id;
      if (!sourceId) continue;
      outgoingBySource.set(sourceId, (outgoingBySource.get(sourceId) ?? 0) + 1);
    }
    const splitCount = [...outgoingBySource.values()].filter((count) => count > 1).length;
    const hasTimerStart = startEvents.some((event) =>
      (event.eventDefinitions ?? []).some((definition) => definition.$type === "bpmn:TimerEventDefinition"),
    );
    const hasMessageStart = startEvents.some((event) =>
      (event.eventDefinitions ?? []).some((definition) => definition.$type === "bpmn:MessageEventDefinition"),
    );
    const auditTasks = taskTypes.filter((type) => type === "generic.audit.emit").length;
    const missingTaskDefinitions = serviceTasks.length - taskTypes.length;
    const complexityScore = serviceTasks.length + gateways.length * 2 + splitCount;
    const straightThrough = gateways.length === 0 && splitCount === 0;

    return {
      processId: process.id ?? "",
      name: process.name ?? "",
      nsid: doc.nsid ?? "",
      sourcePath: relativePath,
      project: projectFromPath(relativePath, bpmnRoot),
      executable: process.isExecutable === true,
      startEventCount: startEvents.length,
      endEventCount: endEvents.length,
      serviceTaskCount: serviceTasks.length,
      gatewayCount: gateways.length,
      sequenceFlowCount: sequenceFlows.length,
      splitCount,
      hasTimerStart,
      hasMessageStart,
      auditTaskCount: auditTasks,
      missingTaskDefinitions,
      taskTypes,
      taskFamilies: taskTypes.map(taskFamily),
      complexityScore,
      variant: straightThrough ? "straight-through" : gateways.length > 0 ? "gateway-controlled" : "multi-start-or-join",
    };
  });
}

function buildFindings(processes) {
  const findings = [];
  for (const process of processes) {
    if (!process.executable) {
      findings.push({ severity: "high", type: "not_executable", process });
    }
    if (process.missingTaskDefinitions > 0) {
      findings.push({ severity: "high", type: "missing_task_definition", process });
    }
    if (process.serviceTaskCount >= 5 && process.gatewayCount === 0) {
      findings.push({ severity: "medium", type: "long_straight_through_flow", process });
    }
    if (process.auditTaskCount === 0) {
      findings.push({ severity: "medium", type: "missing_audit_emit", process });
    }
    if (process.startEventCount > 1 && process.gatewayCount === 0) {
      findings.push({ severity: "low", type: "multi_start_without_gateway", process });
    }
  }
  const order = { high: 0, medium: 1, low: 2 };
  return findings.sort((a, b) =>
    order[a.severity] - order[b.severity] ||
    b.process.complexityScore - a.process.complexityScore ||
    a.process.sourcePath.localeCompare(b.process.sourcePath),
  );
}

function summarize(processes, failures) {
  const taskTypes = processes.flatMap((process) => process.taskTypes);
  const serviceTaskCounts = processes.map((process) => process.serviceTaskCount);
  const complexityScores = processes.map((process) => process.complexityScore);
  const findings = buildFindings(processes);
  return {
    generatedAt: new Date().toISOString(),
    bpmnFiles: new Set(processes.map((process) => process.sourcePath)).size + failures.length,
    parsedProcesses: processes.length,
    parseFailures: failures.length,
    executableProcesses: processes.filter((process) => process.executable).length,
    projects: countBy(processes, (process) => process.project),
    variants: countBy(processes, (process) => process.variant),
    starts: {
      timer: processes.filter((process) => process.hasTimerStart).length,
      message: processes.filter((process) => process.hasMessageStart).length,
      manualOrPlain: processes.filter((process) => !process.hasTimerStart && !process.hasMessageStart).length,
      multipleStarts: processes.filter((process) => process.startEventCount > 1).length,
    },
    tasks: {
      serviceTasks: serviceTaskCounts.reduce((sum, count) => sum + count, 0),
      p50PerProcess: percentile(serviceTaskCounts, 0.5),
      p95PerProcess: percentile(serviceTaskCounts, 0.95),
      maxPerProcess: Math.max(0, ...serviceTaskCounts),
      topTaskTypes: countBy(taskTypes, (type) => type).slice(0, 20),
      topTaskFamilies: countBy(processes.flatMap((process) => process.taskFamilies), (family) => family).slice(0, 20),
    },
    controlFlow: {
      gateways: processes.reduce((sum, process) => sum + process.gatewayCount, 0),
      sequenceFlows: processes.reduce((sum, process) => sum + process.sequenceFlowCount, 0),
      processesWithGateways: processes.filter((process) => process.gatewayCount > 0).length,
      processesWithSplits: processes.filter((process) => process.splitCount > 0).length,
      complexityP50: percentile(complexityScores, 0.5),
      complexityP95: percentile(complexityScores, 0.95),
    },
    observability: {
      withGenericAuditEmit: processes.filter((process) => process.auditTaskCount > 0).length,
      withoutGenericAuditEmit: processes.filter((process) => process.auditTaskCount === 0).length,
      auditTaskCount: processes.reduce((sum, process) => sum + process.auditTaskCount, 0),
    },
    findings,
  };
}

function table(rows, columns) {
  const header = `| ${columns.map((col) => col.label).join(" | ")} |`;
  const align = `| ${columns.map((col) => col.align === "right" ? "---:" : "---").join(" | ")} |`;
  const body = rows.map((row) => `| ${columns.map((col) => String(col.value(row) ?? "")).join(" | ")} |`);
  return [header, align, ...body].join("\n");
}

function renderMarkdown(report, limitFindings) {
  const s = report.summary;
  const topProjects = s.projects.slice(0, 15);
  const topFindings = s.findings.slice(0, limitFindings);
  return `# BPMN Process Mining Snapshot

- generatedAt: ${s.generatedAt}
- BPMN files scanned: ${s.bpmnFiles}
- parsed processes: ${s.parsedProcesses}
- parse failures: ${s.parseFailures}
- executable processes: ${s.executableProcesses}

## Process Model

- variants: ${s.variants.map((row) => `${row.key}=${row.count}`).join(", ")}
- starts: timer=${s.starts.timer}, message=${s.starts.message}, manual/plain=${s.starts.manualOrPlain}, multiple-start=${s.starts.multipleStarts}
- service tasks: total=${s.tasks.serviceTasks}, p50/process=${s.tasks.p50PerProcess}, p95/process=${s.tasks.p95PerProcess}, max/process=${s.tasks.maxPerProcess}
- control flow: gateways=${s.controlFlow.gateways}, sequenceFlows=${s.controlFlow.sequenceFlows}, processesWithGateways=${s.controlFlow.processesWithGateways}, processesWithSplits=${s.controlFlow.processesWithSplits}
- observability: generic.audit.emit present=${s.observability.withGenericAuditEmit}, missing=${s.observability.withoutGenericAuditEmit}, auditTaskCount=${s.observability.auditTaskCount}

## Top Projects

${table(topProjects, [
  { label: "Project", value: (row) => row.key },
  { label: "Processes", align: "right", value: (row) => row.count },
])}

## Top Task Types

${table(s.tasks.topTaskTypes.slice(0, 15), [
  { label: "Task type", value: (row) => row.key },
  { label: "Count", align: "right", value: (row) => row.count },
])}

## Task Families

${table(s.tasks.topTaskFamilies.slice(0, 15), [
  { label: "Family", value: (row) => row.key },
  { label: "Count", align: "right", value: (row) => row.count },
])}

## Findings

${topFindings.length === 0 ? "No findings." : table(topFindings, [
  { label: "Severity", value: (row) => row.severity },
  { label: "Type", value: (row) => row.type },
  { label: "Process", value: (row) => row.process.processId },
  { label: "Project", value: (row) => row.process.project },
  { label: "Tasks", align: "right", value: (row) => row.process.serviceTaskCount },
  { label: "Gateways", align: "right", value: (row) => row.process.gatewayCount },
  { label: "Source", value: (row) => row.process.sourcePath },
])}

## Interpretation

This is model mining from the checked-in BPMN contracts, not runtime event-log mining. Runtime conformance and duration analysis still require OCEL/BPMN activity rows from the deployed workers. The strongest static signal is observability coverage: processes without \`generic.audit.emit\` can run but are harder to mine later from aggregate logs.
`;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const root = path.resolve(opts.root);
  const bpmnAbsRoot = path.resolve(root, opts.bpmnRoot);
  if (!existsSync(bpmnAbsRoot)) throw new Error(`BPMN root not found: ${bpmnAbsRoot}`);

  const moddle = new BpmnModdle();
  const files = await listFiles(bpmnAbsRoot);
  const processes = [];
  const failures = [];
  for (const absPath of files) {
    const xml = readFileSync(absPath, "utf8");
    try {
      const parsed = await moddle.fromXML(xml);
      processes.push(...analyzeProcess({
        root,
        bpmnRoot: opts.bpmnRoot,
        absPath,
        rootElement: parsed.rootElement,
        xml,
      }));
    } catch (error) {
      failures.push({ sourcePath: rel(root, absPath), error: error?.message ?? String(error) });
    }
  }

  const summary = summarize(processes, failures);
  const report = { summary, failures, processes };

  if (opts.out) {
    const outPath = path.resolve(root, opts.out);
    mkdirSync(path.dirname(outPath), { recursive: true });
    const body = opts.out.endsWith(".json") ? JSON.stringify(report, null, 2) : renderMarkdown(report, opts.limitFindings);
    writeFileSync(outPath, `${body.trimEnd()}\n`);
  }

  if (opts.json) {
    console.log(JSON.stringify(report, null, 2));
  } else if (!opts.out) {
    console.log(renderMarkdown(report, opts.limitFindings));
  } else {
    console.log(`process-mining: ${summary.parsedProcesses} processes from ${summary.bpmnFiles} BPMN files`);
    console.log(`process-mining: findings high=${summary.findings.filter((f) => f.severity === "high").length} medium=${summary.findings.filter((f) => f.severity === "medium").length} low=${summary.findings.filter((f) => f.severity === "low").length}`);
    console.log(`process-mining: wrote ${opts.out}`);
  }
}

main().catch((error) => {
  console.error(error?.stack ?? error?.message ?? String(error));
  process.exitCode = 1;
});
