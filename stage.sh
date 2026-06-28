#!/bin/bash
# etzhayyim-py → bb CLI migration (ADR-2606222000) staging helper.
#
# CLI status after the 2606222000 finishing pass (see the ADR migration table):
#   - EVERY python e7m subcommand is now reachable via `bb e7m <cmd>` (cli.cljc):
#       * bonsai/coverage/identifier-audit/source-graph/shannon/kosei-tiers/dns-sync — inline handlers (run green)
#       * actors/agent/agent-runtime/agent-token/apps/authn/authz/bunseki/code-quality/cohort/
#         training/vertex/workspace/xrpc/yoroshiku/vitals/lint — per-twin -main (argv mirrors click)
#       * database/deploy/deps/dodaf/haisen/hinshitsu/identity/kagami/kaizen/kashika/kosei/logs/
#         metrics/mitama/mokuteki/monitor/nono/organism/process-mining/projector/systemofsystem/murakumo
#         — library-dispatch (ns loads + argv parses; live/destructive legs guarded → use the python
#           module's flags via the python e7m for live runs until each twin's live IO leg is parity-verified)
#   - RETIRED: lint.py (full read-only parity in etzhayyim.lint.cljc → `bb e7m lint`) — git rm'd.
#   - The 7 py modules staged below (deps/mitama/database/coverage/bonsai/kashika/actors) + the python
#     test COEXIST: their clj twins are wired for dispatch but their live HTTP/scan legs still run via
#     python, so they are intentionally NOT retired here. Run them via `bb e7m <cmd>` (dispatch) or the
#     python e7m (live). httpx-in-etzhayyim-py remains until those live legs are ported.
git add \
  50-infra/k8s/claim-consumer-actor/README.md \
  50-infra/k8s/atproto-pds/deployment.yaml \
  50-infra/k8s/atproto-pds/RUNBOOK.md \
  50-infra/k8s/atproto-pds/README.md \
  50-infra/k8s/atproto-pds/secrets-template.yaml \
  50-infra/k8s/atproto-pds/bun-entry.ts \
  50-infra/k8s/medical-coverage-ingester/facility-b2-replayer-cronjob.yaml \
  50-infra/k8s/medical-coverage-ingester/facility-b2-replayer-tiny-cronjob.yaml \
  50-infra/k8s/medical-coverage-ingester/kustomization.yaml \
  50-infra/k8s/medical-coverage-ingester/kotoba_datomic.py \
  50-infra/k8s/medical-coverage-ingester/facility-b2-replayer-100-cronjob.yaml \
  50-infra/k8s/medical-coverage-ingester/cronjob.yaml \
  50-infra/k8s/medical-coverage-ingester/README.md \
  50-infra/k8s/medical-coverage-ingester/facility-raw-cronjob.yaml \
  50-infra/k8s/medical-coverage-ingester/ingester.py \
  50-infra/k8s/medical-coverage-ingester/secrets-template.yaml \
  50-infra/k8s/bpmn-dispatcher/configmap-kotodama-sse-fix.yaml \
  50-infra/k8s/bpmn-dispatcher/README.md \
  50-infra/k8s/bpmn-dispatcher/deployment-dispatcher.yaml \
  50-infra/k8s/bpmn-dispatcher/configmap-kotodama-cache-fix.yaml \
  50-infra/k8s/maps-coverage-langgraph/cronjob-cycle.yaml \
  50-infra/k8s/maps-coverage-langgraph/README.md \
  50-infra/k8s/intel-dependency-worker/worker.py \
  50-infra/k8s/intel-dependency-worker/README.md \
  50-infra/k8s/lg-gov/deployment.yaml \
  50-infra/k8s/murakumo-kubelet/README.md \
  50-infra/k8s/legal-corpus-langgraph/legal_corpus_langgraph.py \
  50-infra/k8s/legal-corpus-langgraph/mcp_server.py \
  50-infra/k8s/lg-ses/deployment.yaml \
  50-infra/k8s/maps-osm-ingest/job-japan-dryrun.yaml \
  50-infra/k8s/maps-osm-ingest/cronjob.yaml \
  50-infra/k8s/maps-osm-ingest/README.md \
  50-infra/k8s/maps-osm-ingest/job-planet-bootstrap.yaml \
  50-infra/k8s/maps3d/README.md \
  50-infra/k8s/maps3d/deploy.sh \
  50-infra/k8s/maps3d/workers/_common.py \
  50-infra/k8s/medical-coverage-mcp/deployment.yaml \
  50-infra/k8s/medical-coverage-mcp/kustomization.yaml \
  50-infra/k8s/medical-coverage-mcp/README.md \
  50-infra/k8s/medical-coverage-mcp/mcp_server.py \
  50-infra/k8s/medical-coverage-mcp/secrets-template.yaml \
  50-infra/k8s/medical-coverage-mcp/kotoba_datomic.py \
  50-infra/k8s/bpmn-engine-host/deployment.yaml \
  50-infra/k8s/bpmn-engine-host/RUNBOOK.md \
  50-infra/k8s/bpmn-engine-host/preflight.sh \
  50-infra/k8s/bpmn-engine-host/README.md \
  50-infra/k8s/bpmn-engine-host/engine.py \
  50-infra/k8s/bpmn-engine-host/secrets-template.yaml \
  50-infra/k8s/bpmn-engine-host/tests/README.md \
  50-infra/k8s/bpmn-engine-host/tests/smoke.py \
  50-infra/k8s/bpmn-engine-host/requirements.txt \
  50-infra/k8s/gleif-lei-s3-ingester/kustomization.yaml \
  50-infra/k8s/gleif-lei-s3-ingester/kotoba_datomic.py \
  50-infra/k8s/gleif-lei-s3-ingester/cronjob.yaml \
  70-tools/etzhayyim-py/src/etzhayyim/deps.py \
  70-tools/etzhayyim-py/src/etzhayyim/mitama.py \
  70-tools/etzhayyim-py/src/etzhayyim/database.py \
  70-tools/etzhayyim-py/src/etzhayyim/coverage.py \
  70-tools/etzhayyim-py/src/etzhayyim/bonsai.py \
  70-tools/etzhayyim-py/src/etzhayyim/kashika.py \
  70-tools/etzhayyim-py/src/etzhayyim/actors.py \
  70-tools/etzhayyim-py/tests/test_new_commands.py \
  50-infra/vultr/kotoba/
  
git rm -rf 50-infra/vultr/risingwave/
git status --staged
