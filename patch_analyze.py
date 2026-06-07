import re
import sys

def patch():
    with open('50-infra/k8s/intel-dependency-worker/worker.py', 'r') as f:
        content = f.read()

    # Cleanups
    content = content.replace("import psycopg\n", "")
    content = content.replace("def dict_row_factory() -> Any:\n\n    return psycopg.rows.dict_row", "")

    # IntelStore init
    old_init = """    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def connect(self) -> psycopg.Connection[Any]:
        # RisingWave's PostgreSQL wire path is sensitive to psycopg3 server-side
        # prepared statements (for example LIMIT parameters and some SELECTs).
        # Keep statements simple-protocol unless a future RW version proves safe.
        return psycopg.connect(self.dsn, autocommit=True, prepare_threshold=None)"""
    new_init = """    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        from kotodama.kotoba_datomic import get_kotoba_client
        self.client = get_kotoba_client()"""
    content = content.replace(old_init, new_init)

    # 1. create_run
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+INSERT INTO vertex_intel_inference_run.*?\)\n\s+\)',
        r"""self.client.insert_row("vertex_intel_inference_run", {
                        "vertex_id": vertex_id,
                        "owner_did": OWNER_DID,
                        "run_id": run_id,
                        "trigger_kind": trigger_kind,
                        "scope_json": json_text({"scope": scope, "dryRun": dry_run}),
                        "status": 'running',
                        "started_at": str(now_ms()),
                        "created_at": str(now_ms()),
                        "sensitivity_ord": 1,
                        "org_id": OWNER_DID,
                        "user_id": OWNER_DID,
                        "actor_id": ACTOR_ID
                    })""",
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+INSERT INTO vertex_intel_inference_chain.*?\)\n\s+\)',
        r"""self.client.insert_row("vertex_intel_inference_chain", {
                        "vertex_id": legacy_vertex_id,
                        "owner_did": OWNER_DID,
                        "status": 'running',
                        "chain_id": run_id,
                        "subject_name": scope.get("subjectName") or "scheduled dependency inference",
                        "subject_did": scope.get("subjectDid"),
                        "industry": scope.get("industry"),
                        "source_text": json_text({"scope": scope, "dryRun": dry_run, "triggerKind": trigger_kind}),
                        "steps_count": 0,
                        "cohorts_generated": 0,
                        "org_id": OWNER_DID,
                        "user_id": OWNER_DID,
                        "actor_id": ACTOR_ID,
                        "created_at": str(now_ms())
                    })""",
        content,
        flags=re.DOTALL
    )

    # 2. materialize_topology_dependencies
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+INSERT INTO edge_intel_dependency.*?\)\n\s+\)',
        r"""self.client.insert_row("edge_intel_dependency", {
                        "edge_id": edge_id,
                        "owner_did": OWNER_DID,
                        "src_vid": edge.src_vid,
                        "dst_vid": edge.dst_vid,
                        "predicate": 'depends_on',
                        "dependency_kind": edge.edge_table,
                        "confidence": edge.confidence,
                        "evidence_count": len(edge.evidence),
                        "evidence_json": json_text(edge.evidence),
                        "inference_run_id": run_id,
                        "reason": edge.reason,
                        "model_version": 'topology-daemon-v1',
                        "status": "active" if edge.confidence >= 0.75 else "candidate",
                        "created_at": str(now_ms()),
                        "sensitivity_ord": 1,
                        "org_id": OWNER_DID,
                        "user_id": OWNER_DID,
                        "actor_id": ACTOR_ID
                    })""",
        content,
        flags=re.DOTALL,
        count=1
    )

    # 3. materialize_topology_order
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+DELETE FROM vertex_dependency_topology_order.*?\(graph_scope, row\.vertex_id\),\n\s+\)',
        r"""self.client.q(
                    "DELETE FROM vertex_dependency_topology_order WHERE graph_scope = %s AND vertex_id = %s",
                    (graph_scope, row.vertex_id),
                )""",
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+INSERT INTO vertex_dependency_topology_order.*?\)\n\s+\)',
        r"""self.client.insert_row("vertex_dependency_topology_order", {
                        "graph_scope": graph_scope,
                        "vertex_id": row.vertex_id,
                        "owner_did": OWNER_DID,
                        "display_name": row.display_name,
                        "vertex_kind": row.vertex_kind,
                        "topo_rank": row.topo_rank,
                        "reverse_topo_rank": row.reverse_topo_rank,
                        "topo_level": row.topo_level,
                        "dependency_count": row.dependency_count,
                        "dependent_count": row.dependent_count,
                        "unresolved_dependency_count": row.unresolved_dependency_count,
                        "cycle_status": row.cycle_status,
                        "computed_at": utc_iso(),
                        "algorithm": 'kahn-v1-python',
                        "payload_json": row.payload_json,
                        "sensitivity_ord": 1,
                        "created_date": utc_date()
                    })""",
        content,
        flags=re.DOTALL
    )

    # 4. materialize
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+INSERT INTO edge_intel_dependency.*?\)\n\s+\)',
        r"""self.client.insert_row("edge_intel_dependency", {
                            "edge_id": edge_id,
                            "owner_did": OWNER_DID,
                            "src_vid": c.src_vid,
                            "dst_vid": c.dst_vid,
                            "predicate": c.predicate,
                            "dependency_kind": c.dependency_kind,
                            "confidence": c.confidence,
                            "evidence_count": len(c.evidence),
                            "evidence_json": json_text(c.evidence),
                            "inference_run_id": run_id,
                            "reason": c.reason,
                            "model_version": 'intel-dependency-worker-v1',
                            "status": status,
                            "created_at": str(now_ms()),
                            "sensitivity_ord": 1,
                            "org_id": OWNER_DID,
                            "user_id": OWNER_DID,
                            "actor_id": ACTOR_ID
                        })""",
        content,
        flags=re.DOTALL,
        count=1
    )
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+UPDATE vertex_intel_inference_run.*?\)\n\s+\)',
        r"""self.client.q(
                    "UPDATE vertex_intel_inference_run SET candidate_count = %s, active_count = %s, review_count = %s, status = 'completed', completed_at = %s WHERE vertex_id = %s",
                    (len(candidates), active, review, str(now_ms()), run_vertex_id),
                )""",
        content,
        flags=re.DOTALL
    )

    # 5. materialize_legacy
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+INSERT INTO vertex_intel_inferred_cohort.*?\)\n\s+\)',
        r"""self.client.insert_row("vertex_intel_inferred_cohort", {
                    "vertex_id": vertex_id,
                    "owner_did": OWNER_DID,
                    "status": status,
                    "cohort_id": cohort_id,
                    "chain_id": run_id,
                    "target_domain": 'dependency',
                    "entity_type": c.dependency_kind,
                    "layer": 1,
                    "estimated_count": 1,
                    "confidence": c.confidence,
                    "methodology": 'maps-ownership-lei',
                    "inference_rule": c.predicate,
                    "input_fact": c.src_vid,
                    "assumptions": json_text({"dst": c.dst_vid, "evidence": c.evidence, "reason": c.reason}),
                    "cohort_hash": stable_id("hash", candidate_to_dict(c)),
                    "subject_did": c.dst_vid,
                    "subject_name": c.dst_vid,
                    "org_id": OWNER_DID,
                    "user_id": OWNER_DID,
                    "actor_id": ACTOR_ID,
                    "created_at": str(now_ms())
                })""",
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+UPDATE vertex_intel_inference_chain.*?\)\n\s+\)',
        r"""self.client.q(
            "UPDATE vertex_intel_inference_chain SET status = 'completed', steps_count = 4, cohorts_generated = %s WHERE vertex_id = %s",
            (len(candidates), chain_vertex_id),
        )""",
        content,
        flags=re.DOTALL
    )

    # 6. insert_open_lei_entity
    content = re.sub(
        r'cur\.execute\(\n\s+"""\n\s+INSERT INTO vertex_open_lei_entity.*?\)\n\s+\)',
        r"""self.client.insert_row("vertex_open_lei_entity", {
                        "vertex_id": row["vertex_id"],
                        "_seq": None,
                        "created_date": utc_date(),
                        "sensitivity_ord": 1,
                        "owner_did": "did:web:open-lei.etzhayyim.com",
                        "lei": row["lei"],
                        "legal_name": row["legal_name"],
                        "country": row.get("country"),
                        "legal_form": row.get("legal_form"),
                        "registration_authority": row.get("registration_authority"),
                        "registration_status": row.get("registration_status") or "UNKNOWN",
                        "issued_at": row.get("issued_at"),
                        "next_renewal_at": row.get("next_renewal_at"),
                        "status": row.get("status") or "active",
                        "created_at": row.get("created_at") or utc_iso(),
                        "org_id": "did:web:open-lei.etzhayyim.com",
                        "user_id": "did:web:open-lei.etzhayyim.com",
                        "actor_id": "sys.langserver.intel.gleif"
                    })""",
        content,
        flags=re.DOTALL
    )

    # SELECT Replacements
    # We replace `with self.connect() as conn, conn.cursor(...) as cur:` with `if True:`
    # And then `cur.execute(...)` `cur.fetchall()` with `self.client.q(...)`
    
    content = re.sub(r"with self\.connect\(\) as conn, conn\.cursor\((?:row_factory=dict_row_factory\(\))?\) as cur:", "if True:", content)
    content = re.sub(r"with self\.connect\(\) as conn, conn\.cursor\(\) as cur:", "if True:", content)
    
    # Specific SELECT replacements
    content = re.sub(r"cur\.execute\(\n\s+(.*?)\n\s+\)\n\s+return list\(cur\.fetchall\(\)\)", r"return list(self.client.q(\1))", content, flags=re.DOTALL)
    content = re.sub(r"cur\.execute\((.*?)\)\n\s+rows = cur\.fetchall\(\)", r"rows = self.client.q(\1)", content, flags=re.DOTALL)
    content = re.sub(r"cur\.execute\(\n\s+(.*?)\n\s+\)\n\s+rows = cur\.fetchall\(\)", r"rows = self.client.q(\1)", content, flags=re.DOTALL)
    content = re.sub(r"cur\.execute\((.*?)\)\n\s+row = cur\.fetchone\(\)", r"rows = self.client.q(\1)\n            row = rows[0] if rows else None", content, flags=re.DOTALL)
    content = re.sub(r"cur\.execute\((.*?)\)", r"self.client.q(\1)", content)

    # Replace self.materialize_legacy signature
    content = content.replace("def materialize_legacy(self, cur: Any, run_id: str, candidates: list[Candidate]) -> tuple[int, int]:", "def materialize_legacy(self, run_id: str, candidates: list[Candidate]) -> tuple[int, int]:")
    content = content.replace("self.materialize_legacy(cur, run_id, candidates)", "self.materialize_legacy(run_id, candidates)")

    with open('50-infra/k8s/intel-dependency-worker/worker.py', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    patch()
