from __future__ import annotations

import http.server
import importlib.util
import json
import threading
import unittest
from unittest import mock

import worker


class FakeStore:
    def __init__(self) -> None:
        self.materialized: list[worker.Candidate] = []

    def create_run(self, scope: dict, trigger_kind: str, dry_run: bool) -> dict:
        self.scope = scope
        self.trigger_kind = trigger_kind
        self.dry_run = dry_run
        return {"runId": "intel-run-test"}

    def scan_candidates(self, scope: dict, max_candidates: int) -> list[worker.Candidate]:
        self.max_candidates = max_candidates
        return [
            worker.Candidate(
                src_vid="building-1",
                dst_vid="owner-lei",
                predicate="owned_by",
                dependency_kind="building_owner_lei",
                confidence=0.86,
                evidence=[{"source": "maps.edge_ownership", "lei": "549300TEST"}],
                reason="LEI backed owner",
            ),
            worker.Candidate(
                src_vid="building-2",
                dst_vid="owner-no-lei",
                predicate="owned_by",
                dependency_kind="building_owner",
                confidence=0.72,
                evidence=[{"source": "maps.edge_ownership"}],
                reason="registry owner",
            ),
            worker.Candidate(
                src_vid="building-3",
                dst_vid="not-valid",
                predicate="mentions",
                dependency_kind="noise",
                confidence=0.99,
                evidence=[],
                reason="invalid predicate",
            ),
        ]

    def materialize(self, run_id: str, candidates: list[worker.Candidate], dry_run: bool) -> dict:
        self.materialized = candidates
        return {
            "candidateCount": len(candidates),
            "activeCount": sum(1 for c in candidates if c.confidence >= 0.85),
            "reviewCount": sum(1 for c in candidates if c.confidence < 0.85),
            "dryRun": dry_run,
        }


class FakeTopologyStore:
    def __init__(self) -> None:
        self.materialized_edges: list[worker.TopologyEdge] = []
        self.materialized_order: list[worker.TopologyOrderRow] = []

    def create_run(self, scope: dict, trigger_kind: str, dry_run: bool) -> dict:
        self.scope = scope
        self.trigger_kind = trigger_kind
        self.dry_run = dry_run
        return {"runId": "topology-run-test"}

    def scan_topology_nodes(self, graph_scope: str, max_nodes_per_table: int) -> list[worker.TopologyNode]:
        self.graph_scope = graph_scope
        self.max_nodes_per_table = max_nodes_per_table
        return [
            worker.TopologyNode("actor:planner", "actor", "Planner", "actor_registry"),
            worker.TopologyNode("vertex:schema", "schema", "Schema", "vertex_schema"),
            worker.TopologyNode("vertex:build", "job", "Build", "vertex_job"),
            worker.TopologyNode("vertex:deploy", "job", "Deploy", "vertex_job"),
        ]

    def scan_topology_edges(self, graph_scope: str, max_edges_per_table: int) -> list[worker.TopologyEdge]:
        self.max_edges_per_table = max_edges_per_table
        return [
            worker.TopologyEdge(
                "edge-build-schema",
                "vertex:build",
                "vertex:schema",
                "edge_job_requires_schema",
                "depends_on",
                "src_depends_on_dst",
                0.88,
                [{"sourceTable": "edge_job_requires_schema"}],
                "requires relation",
            ),
            worker.TopologyEdge(
                "edge-deploy-build",
                "vertex:deploy",
                "vertex:build",
                "edge_actor_triggers_job",
                "actor_triggers_job",
                "unknown",
                0.25,
                [{"sourceTable": "edge_actor_triggers_job"}],
                "ambiguous relation",
            ),
        ]

    def infer_topology_dependencies_with_llm(
        self,
        edges: list[worker.TopologyEdge],
        max_edges: int,
    ) -> list[worker.TopologyEdge]:
        return worker.IntelStore.infer_topology_dependencies_with_llm(self, edges, max_edges)  # type: ignore[arg-type]

    def materialize_topology_dependencies(
        self,
        graph_scope: str,
        run_id: str,
        edges: list[worker.TopologyEdge],
        dry_run: bool,
    ) -> dict:
        self.materialized_edges = edges
        return {"dependencyEdgeCount": len(edges), "dryRun": dry_run}

    def materialize_topology_order(
        self,
        graph_scope: str,
        rows: list[worker.TopologyOrderRow],
        dry_run: bool,
    ) -> dict:
        self.materialized_order = rows
        return {"topologyOrderCount": len(rows), "dryRun": dry_run}


class IntelWorkerIntegrationTest(unittest.TestCase):
    def test_run_pipeline_filters_scores_and_splits_review(self) -> None:
        store = FakeStore()
        result = worker.run_pipeline(
            store=store,  # type: ignore[arg-type]
            scope={"buildingVertexId": "building-1"},
            trigger_kind="scheduled",
            max_candidates=10,
            dry_run=True,
        )

        self.assertEqual(result["runId"], "intel-run-test")
        self.assertEqual(result["candidateCount"], 2)
        self.assertEqual(result["activeCount"], 1)
        self.assertEqual(result["reviewCount"], 1)
        self.assertTrue(result["dryRun"])
        self.assertEqual([c.predicate for c in store.materialized], ["owned_by", "owned_by"])

    def test_dependency_row_to_graph_response(self) -> None:
        graph = worker.rows_to_graph([
            {
                "edge_id": "edge-1",
                "src_vid": "building-1",
                "dst_vid": "owner-1",
                "predicate": "owned_by",
                "dependency_kind": "building_owner_lei",
                "confidence": 0.86,
                "evidence_count": 1,
                "evidence_json": '[{"source":"maps.edge_ownership"}]',
                "status": "active",
                "src_label": "Building A",
                "src_kind": "building",
                "dst_label": "Owner Corp",
                "dst_kind": "legal_entity",
                "dst_lei": "549300TEST",
            }
        ])

        self.assertEqual(len(graph["nodes"]), 2)
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual(graph["edges"][0]["edgeId"], "edge-1")
        self.assertEqual(graph["edges"][0]["evidence"][0]["source"], "maps.edge_ownership")

    def test_entity_candidate_scores_identifier_and_name_matches(self) -> None:
        lei_match = worker.entity_candidate(
            vertex_id="lei-owner",
            name="Owner Corp",
            entity_kind="legal_entity",
            source="test",
            query="Owner",
            lei="549300TEST",
            hints={"lei": "549300TEST"},
        )
        exact_name = worker.entity_candidate(
            vertex_id="name-owner",
            name="Owner Corp",
            entity_kind="legal_entity",
            source="test",
            query="Owner Corp",
        )
        fuzzy_name = worker.entity_candidate(
            vertex_id="fuzzy-owner",
            name="Owner Corporation Holdings",
            entity_kind="legal_entity",
            source="test",
            query="Owner Corporation",
        )

        self.assertEqual(lei_match["score"], 0.98)
        self.assertEqual(exact_name["score"], 0.94)
        self.assertGreater(fuzzy_name["score"], 0.8)

    def test_llm_rerank_is_disabled_without_env(self) -> None:
        candidates = [
            {"entityId": "a", "score": 0.7},
            {"entityId": "b", "score": 0.6},
        ]
        self.assertEqual(worker.maybe_rerank_entities_with_llm("query", candidates, {}), candidates)

    def test_dependency_hint_classifies_requires_and_topology_only_edges(self) -> None:
        requires = worker.dependency_hint("edge_robotics_package_requires_material")
        contains = worker.dependency_hint("edge_bpmn_contains")

        self.assertTrue(requires["isDependency"])
        self.assertEqual(requires["direction"], "src_depends_on_dst")
        self.assertFalse(contains["isDependency"])
        self.assertEqual(contains["direction"], "topology_only")

    def test_compute_topology_order_uses_dependency_direction(self) -> None:
        rows = worker.compute_topology_order(
            "test",
            [
                worker.TopologyNode("deploy", "action", "Deploy", "vertex_action"),
                worker.TopologyNode("build", "action", "Build", "vertex_action"),
                worker.TopologyNode("schema", "action", "Schema", "vertex_action"),
            ],
            [
                worker.TopologyEdge("e1", "deploy", "build", "edge_depends_on", "depends_on", "src_depends_on_dst", 0.95, [], ""),
                worker.TopologyEdge("e2", "build", "schema", "edge_depends_on", "depends_on", "src_depends_on_dst", 0.95, [], ""),
            ],
        )

        self.assertEqual([row.vertex_id for row in rows], ["schema", "build", "deploy"])
        self.assertEqual([row.reverse_topo_rank for row in rows], [2, 1, 0])
        self.assertEqual(rows[-1].dependency_count, 1)

    def test_compute_topology_order_marks_cycles(self) -> None:
        rows = worker.compute_topology_order(
            "test",
            [worker.TopologyNode("a", "action", "A", "vertex_action"), worker.TopologyNode("b", "action", "B", "vertex_action")],
            [
                worker.TopologyEdge("e1", "a", "b", "edge_depends_on", "depends_on", "src_depends_on_dst", 0.95, [], ""),
                worker.TopologyEdge("e2", "b", "a", "edge_depends_on", "depends_on", "src_depends_on_dst", 0.95, [], ""),
            ],
        )

        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row.cycle_status == "cycle_member" for row in rows))

    def test_topology_pipeline_scans_resolves_orders_and_materializes(self) -> None:
        if importlib.util.find_spec("litellm") is None:
            self.skipTest("litellm is not installed")

        requests: list[dict] = []

        class LiteLLMHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("content-length") or "0")
                body = self.rfile.read(length)
                requests.append(json.loads(body))
                response = {
                    "id": "chatcmpl-topology-test",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "test-topology-model",
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {
                                "role": "assistant",
                                "content": json.dumps({
                                    "edges": [
                                        {
                                            "edge_id": "edge-deploy-build",
                                            "isDependency": True,
                                            "confidence": 0.91,
                                            "reason": "deployment must wait for build output",
                                        }
                                    ]
                                }),
                            },
                        }
                    ],
                }
                payload = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), LiteLLMHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        store = FakeTopologyStore()

        try:
            with mock.patch.dict(
                worker.os.environ,
                {
                    "INTEL_TOPOLOGY_LLM_RESOLVE": "true",
                    "INTEL_LLM_URL": f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                    "INTEL_LLM_MODEL": "test-topology-model",
                    "INTEL_LLM_API_KEY": "sk-test",
                    "INTEL_LLM_TIMEOUT_SEC": "5",
                },
                clear=False,
            ):
                result = worker.run_topology_analysis_pipeline(
                    store=store,  # type: ignore[arg-type]
                    scope={
                        "graphScope": "integration",
                        "maxNodesPerTable": 10,
                        "maxEdgesPerTable": 10,
                        "llmEdgeLimit": 10,
                    },
                    trigger_kind="integration_test",
                    dry_run=False,
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(result["runId"], "topology-run-test")
        self.assertEqual(result["graphScope"], "integration")
        self.assertEqual(result["nodeCount"], 4)
        self.assertEqual(result["scannedEdgeCount"], 2)
        self.assertEqual(result["dependencyEdgeCount"], 2)
        self.assertEqual(result["topologyOrderCount"], 4)
        self.assertEqual(result["cycleMemberCount"], 0)
        self.assertFalse(result["dryRun"])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["model"], "test-topology-model")
        self.assertIn("messages", requests[0])

        self.assertEqual([edge.edge_id for edge in store.materialized_edges], ["edge-build-schema", "edge-deploy-build"])
        self.assertEqual(store.materialized_edges[1].predicate, "depends_on")
        self.assertEqual(store.materialized_edges[1].confidence, 0.91)
        self.assertIn("LLM topology resolver", store.materialized_edges[1].reason)
        self.assertEqual(
            [row.vertex_id for row in store.materialized_order],
            ["actor:planner", "vertex:schema", "vertex:build", "vertex:deploy"],
        )
        by_vertex_id = {row.vertex_id: row for row in store.materialized_order}
        self.assertEqual(by_vertex_id["vertex:deploy"].dependency_count, 1)
        self.assertEqual(by_vertex_id["vertex:schema"].dependent_count, 1)
        self.assertEqual(by_vertex_id["vertex:deploy"].reverse_topo_rank, 0)

    def test_live_llm_etzhayyim_ai_json_completion(self) -> None:
        if importlib.util.find_spec("litellm") is None:
            self.skipTest("litellm is not installed")
        if not worker.bool_env("INTEL_RUN_LIVE_LLM_INTEGRATION", False):
            self.skipTest("set INTEL_RUN_LIVE_LLM_INTEGRATION=true to call llm.etzhayyim.com")

        with mock.patch.dict(
            worker.os.environ,
            {
                "INTEL_LLM_URL": "https://llm.etzhayyim.com/v1/chat/completions",
                "INTEL_LLM_MODEL": worker.os.environ.get("INTEL_LLM_MODEL", "gemma4-runpod"),
                "INTEL_LLM_MAGATAMA_VERIFIED": "true",
                "INTEL_LLM_CREDITS_DID": worker.os.environ.get("INTEL_LLM_CREDITS_DID", "did:web:llm.etzhayyim.com"),
                "INTEL_LLM_TIMEOUT_SEC": worker.os.environ.get("INTEL_LLM_TIMEOUT_SEC", "90"),
            },
            clear=False,
        ):
            result = worker.call_llm_json(
                "Return strict JSON only.",
                'Return exactly this JSON object: {"ok":true}',
                max_tokens=40,
            )

        self.assertEqual(result, {"ok": True})

    def test_entity_resolver_uses_open_lei_projection_before_legacy_table(self) -> None:
        class ResolverStore(worker.IntelStore):
            def __init__(self) -> None:
                super().__init__("postgres://example")
                self.calls: list[str] = []

            def resolve_entity_from_contracts_organizations(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                self.calls.append("contracts")
                return []

            def resolve_entity_from_open_lei_entities(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                self.calls.append("open_lei")
                return [
                    worker.entity_candidate(
                        vertex_id="open-lei-owner",
                        name="Owner Corp",
                        entity_kind="legal_entity",
                        source="vertex_open_lei_entity",
                        query=query,
                        lei=hints.get("lei"),
                        hints=hints,
                    )
                ]

            def resolve_entity_from_entity_dids(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                self.calls.append("entity_did")
                return []

            def resolve_entity_from_subjects(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                self.calls.append("subject")
                return []

            def resolve_entity_from_legal_entities(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                self.calls.append("legacy_legal_entity")
                return []

        store = ResolverStore()
        result = store.resolve_entity("run-1", "010G7UHBHEI87EKP0Q97", "legal_entity", {"lei": "010G7UHBHEI87EKP0Q97"}, 1)

        self.assertEqual(result["candidateCount"], 1)
        self.assertEqual(result["candidates"][0]["source"], "vertex_open_lei_entity")
        self.assertEqual(store.calls, ["contracts", "open_lei"])

    def test_entity_resolver_lazily_populates_open_lei_from_gleif_exact_lei(self) -> None:
        class ResolverStore(worker.IntelStore):
            def __init__(self) -> None:
                super().__init__("postgres://example")
                self.inserted: list[dict] = []

            def resolve_entity_from_contracts_organizations(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                return []

            def resolve_entity_from_open_lei_entities(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                return []

            def resolve_entity_from_entity_dids(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                return []

            def resolve_entity_from_subjects(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                return []

            def resolve_entity_from_legal_entities(self, query, entity_kind, hints, limit):  # type: ignore[no-untyped-def]
                return []

            def insert_open_lei_entity(self, row):  # type: ignore[no-untyped-def]
                self.inserted.append(row)

        gleif_row = {
            "vertex_id": "at://did:web:open-lei.etzhayyim.com/com.etzhayyim.apps.openLei.entity/HWUPKR0MPOU8FGXBT394",
            "lei": "HWUPKR0MPOU8FGXBT394",
            "legal_name": "Apple Inc.",
            "country": "US",
            "registration_status": "ISSUED",
            "status": "active",
        }
        store = ResolverStore()
        with mock.patch.object(worker, "fetch_gleif_lei_record", return_value=gleif_row):
            result = store.resolve_entity("run-1", "", "legal_entity", {"lei": "HWUPKR0MPOU8FGXBT394"}, 1)

        self.assertEqual(result["candidateCount"], 1)
        self.assertEqual(result["candidates"][0]["lei"], "HWUPKR0MPOU8FGXBT394")
        self.assertEqual(result["candidates"][0]["source"], "vertex_open_lei_entity")
        self.assertEqual(store.inserted, [gleif_row])


if __name__ == "__main__":
    unittest.main()
