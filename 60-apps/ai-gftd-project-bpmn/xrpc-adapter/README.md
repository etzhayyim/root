# bpmn XRPC Adapter

CF Worker that exposes the 13 rw-free commands as XRPC endpoints.

## Endpoints

**Process (6):**
- `POST /xrpc/ai.gftd.bpmn.deployProcess` — deploy BPMN
- `GET /xrpc/ai.gftd.bpmn.listProcesses` — list processes
- `POST /xrpc/ai.gftd.bpmn.validateXml` — validate XML
- `POST /xrpc/ai.gftd.bpmn.compileJsonToXml` — JSON→XML
- `POST /xrpc/ai.gftd.bpmn.compileBpmn` — compile
- `POST /xrpc/ai.gftd.bpmn.analyzeProcess` — analyze

**Instance (6):**
- `POST /xrpc/ai.gftd.bpmn.startInstance` — start
- `GET /xrpc/ai.gftd.bpmn.getInstanceState` — state
- `GET /xrpc/ai.gftd.bpmn.listInstances` — list
- `POST /xrpc/ai.gftd.bpmn.signalInstance` — signal
- `POST /xrpc/ai.gftd.bpmn.cancelInstance` — cancel
- `POST /xrpc/ai.gftd.bpmn.executePipeline` — pipeline

**Activity (1):**
- `GET /xrpc/ai.gftd.bpmn.getActivityLog` — audit log

## Setup & Deploy

```bash
cd 60-apps/ai-gftd-project-bpmn/xrpc-adapter
npm install && wrangler deploy
```

See ADR-2605210000 for design context.
