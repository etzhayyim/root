# BPMN SDK Integration

Status: **Phase δ — partial.** Python `YobelOrchestrator` drives execution (production path). BPMN XML at `yobel-rite-lifecycle.bpmn` is consumed by `@etzhayyim/bpmn-sdk-importer` for documentation, audit visualization, and validation that the cell call sequence matches the documented process — but it does **not** own execution at S2.

## Why two orchestrators

| Layer | Owner | What it does |
|---|---|---|
| **Python `YobelOrchestrator`** | `20-actors/yobel/orchestrator.py` | Drives cell execution: declare → enroll fan-out → release → audit. Calls cell `build_graph()` lazily, manages checkpointer + ports. The actual runtime. |
| **BPMN XML + bpmn-sdk** | `bpmn/yobel-rite-lifecycle.bpmn` + `@etzhayyim/bpmn-sdk-{importer,runtime}` | Process documentation, audit-trail visualization, contract for what the orchestrator MUST do. Compile-time consistency check. |

Both descriptions are kept in 1:1 alignment manually (commit-time review). When BPMN XML diverges from Python orchestrator behavior, that's a bug.

## Why not Python-from-BPMN at S2

The straightforward approach — let `@etzhayyim/bpmn-sdk-runtime` drive execution and dispatch service tasks to Python handlers — would require:

1. **Cross-language IPC**: the TS runtime calls into Python cells. Options: subprocess + JSON stdin/stdout, HTTP localhost, gRPC. All add latency + failure modes.
2. **State synchronization**: BPMN process state (variables, instance ID, currentActivities) lives in the TS runtime; LangGraph cell state lives in the Python checkpointer. Keeping them in sync requires duplicate state machine logic.
3. **Test infrastructure**: a full integration test would need both Python (pytest + langgraph) and TS (jest/vitest + @etzhayyim/bpmn-sdk-*) test harnesses. The current `20-actors/yobel/` is Python-only.

At S2, the cost/benefit doesn't favor cross-language orchestration. The Python orchestrator is direct, debuggable, and matches the BPMN XML structure 1:1 by construction.

## When to add full bpmn-sdk integration

S3+ scenarios where the BPMN runtime is worth the cross-language overhead:

- Multi-actor processes — when a yobel rite involves coordination with non-yobel actors (kuni-umi land coordination during yobel_50yr, lawfirm court filings during political_amnesty), a shared BPMN runtime simplifies cross-actor message correlation
- Human task integration — `@etzhayyim/bpmn-sdk-human` provides the council deliberation human-task UI, which would otherwise need a separate Python implementation
- Form-driven rite declaration — `@etzhayyim/bpmn-sdk-form` for the rite-declaration UI

## How to wire it when needed

Reference pattern (S3 design sketch — not implemented):

```typescript
// 20-actors/yobel/orchestrator-bpmn-sdk.ts
import { importFromXml } from '@etzhayyim/bpmn-sdk-importer';
import { BpmnRuntime } from '@etzhayyim/bpmn-sdk-runtime';
import { readFileSync } from 'node:fs';
import { spawn } from 'node:child_process';

const BPMN_XML = readFileSync(__dirname + '/bpmn/yobel-rite-lifecycle.bpmn', 'utf-8');

// Map BPMN serviceTask implementation to Python cell module
const CELL_DISPATCH = {
  'cell:rite_declaration': '20-actors/yobel/cells/rite_declaration/cell.py',
  'cell:creditor_enrollment': '20-actors/yobel/cells/creditor_enrollment/cell.py',
  'cell:debtor_enrollment': '20-actors/yobel/cells/debtor_enrollment/cell.py',
  'cell:release_settlement': '20-actors/yobel/cells/release_settlement/cell.py',
  'cell:audit_witness': '20-actors/yobel/cells/audit_witness/cell.py',
};

export async function runYobelLifecycle(riteInput: any, creditors: any[], debtors: any[], releases: any[]) {
  const ir = await importFromXml(BPMN_XML);
  const runtime = new BpmnRuntime();

  runtime.onEvent(async (event) => {
    if (event.type !== 'activity.start') return;
    const taskId = event.activityId;  // e.g. 'Task_RiteDeclaration'
    // Look up serviceTask.implementation from BPMN IR
    const cellModule = lookupCellModule(ir, taskId);  // returns 'cell:rite_declaration' etc.
    const cellPath = CELL_DISPATCH[cellModule];
    if (!cellPath) return;
    // Subprocess the Python cell with the event payload as stdin
    const result = await pythonCellInvoke(cellPath, event.variables);
    // Inject result back into BPMN process variables
    // (placeholder — requires BpmnRuntime.setVariables API which is also placeholder at S2)
  });

  const processId = await runtime.deployProcess(ir);
  const context = await runtime.startInstance(processId, {
    variables: { riteInput, creditors, debtors, releases }
  });
  return context;
}

function pythonCellInvoke(cellPath: string, vars: any): Promise<any> {
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', ['-c', `
import json, sys
sys.path.insert(0, '20-actors')
from yobel.cells.rite_declaration.cell import build_graph  # one example
# ... actually dispatch to correct cell, build minimal port stubs, invoke
print(json.dumps({"ok": True}))  # placeholder
`], { stdio: ['pipe', 'pipe', 'pipe'] });
    let out = '';
    proc.stdin.write(JSON.stringify(vars));
    proc.stdin.end();
    proc.stdout.on('data', (d) => { out += d; });
    proc.on('close', (code) => code === 0 ? resolve(JSON.parse(out)) : reject(new Error(`exit ${code}`)));
  });
}
```

Then a small test under `20-actors/yobel/tests_integration/test_bpmn_sdk_dispatch.test.ts` (vitest) deploying the BPMN against a stub runtime + verifying handler dispatch order matches `bpmn/yobel-rite-lifecycle.bpmn`.

## Current state — what bpmn-sdk DOES do for yobel at S2

- Importer parses `bpmn/yobel-rite-lifecycle.bpmn` → IR for documentation tools (e.g. yoro Protocol Canvas BPMN viewer)
- Validation: `@etzhayyim/bpmn-sdk-validation` could check that the BPMN XML is well-formed (not currently wired into yobel CI)
- Export: `@etzhayyim/bpmn-sdk-compiler` round-trip — verify the XML we hand-wrote parses + re-compiles equivalently (not currently wired either)

For audit / Council review, the BPMN XML is the source of truth that documents what the orchestrator does. The Python orchestrator is the source of truth for actual behavior.

## See also

- `bpmn/yobel-rite-lifecycle.bpmn` — the BPMN XML
- `orchestrator.py` — the Python runtime
- `20-actors/etzhayyim-bpmn-sdk/packages/runtime/` — the BPMN runtime API surface
- `20-actors/etzhayyim-bpmn-sdk/examples/e2e-minimal/` — reference for `deployAndStart` flow
