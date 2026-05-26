# bpmn XRPC Adapter

CF Worker that exposes the 13 rw-free commands as XRPC endpoints.

## Endpoints

**Process (6):**
- `POST /xrpc/app.etzhayyim.bpmn.deployProcess` — deploy BPMN
- `GET /xrpc/app.etzhayyim.bpmn.listProcesses` — list processes
- `POST /xrpc/app.etzhayyim.bpmn.validateXml` — validate XML
- `POST /xrpc/app.etzhayyim.bpmn.compileJsonToXml` — JSON→XML
- `POST /xrpc/app.etzhayyim.bpmn.compileBpmn` — compile
- `POST /xrpc/app.etzhayyim.bpmn.analyzeProcess` — analyze

**Instance (6):**
- `POST /xrpc/app.etzhayyim.bpmn.startInstance` — start
- `GET /xrpc/app.etzhayyim.bpmn.getInstanceState` — state
- `GET /xrpc/app.etzhayyim.bpmn.listInstances` — list
- `POST /xrpc/app.etzhayyim.bpmn.signalInstance` — signal
- `POST /xrpc/app.etzhayyim.bpmn.cancelInstance` — cancel
- `POST /xrpc/app.etzhayyim.bpmn.executePipeline` — pipeline

**Activity (1):**
- `GET /xrpc/app.etzhayyim.bpmn.getActivityLog` — audit log

## Setup & Deploy

```bash
cd 60-apps/ai-gftd-project-bpmn/xrpc-adapter
npm install && wrangler deploy
```

See ADR-2605210000 for design context.
