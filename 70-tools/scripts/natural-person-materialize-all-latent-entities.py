#!/usr/bin/env python3
import os
import sys
import time

import psycopg # kotoba-datomic-projection: historical offline script


BATCH_SIZE = int(os.environ.get("NP_LATENT_BATCH_SIZE", "100000"))
BATCHES_PER_RUN = int(os.environ.get("NP_LATENT_BATCHES_PER_RUN", "1"))
DATABASE_URL = os.environ["KOTOBA_URL"]


def _check_rw_ready(cur: psycopg.Cursor) -> bool:  # type: ignore[type-arg]
    """Return False and exit 0 if RisingWave is in recovery (DML blocked)."""
    try:
        cur.execute("SELECT 1")
        cur.fetchone()
        return True
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if "recovery" in msg or "not permitted" in msg or "dml" in msg:
            print(f"rwRecovery=true skipping: {exc}")
            sys.exit(0)
        raise


def main() -> None:
    started = time.time()
    total_inserted = 0
    total_advanced = 0
    with psycopg.connect(DATABASE_URL, autocommit=True, prepare_threshold=0) as conn:
        with conn.cursor() as cur:
            _check_rw_ready(cur)

            cur.execute(
                f"""
                INSERT INTO vertex_natural_person_latent_materialization_cursor (
                  vertex_id, _seq, sensitivity_ord, owner_did, actor_did, org_did,
                  created_at, updated_at, cohort_vid, cohort_hash, target_count,
                  next_ordinal, materialized_count, batch_size, status
                )
                SELECT
                  'at://did:web:natural-person.etzhayyim.com/com.etzhayyim.apps.naturalPerson.latentCursor/' || c.cohort_hash,
                  1, 300,
                  'did:web:natural-person.etzhayyim.com',
                  'did:web:natural-person.etzhayyim.com',
                  'did:web:natural-person.etzhayyim.com',
                  NOW(), NOW(), c.vertex_id, c.cohort_hash,
                  GREATEST(COALESCE(c.intel_estimated_count, 0), 0),
                  1, 0, {int(BATCH_SIZE)},
                  CASE
                    WHEN GREATEST(COALESCE(c.intel_estimated_count, 0), 0) > 0
                    THEN 'active'
                    ELSE 'complete'
                  END
                FROM vertex_natural_person_cohort_person c
                WHERE c.cohort_hash IS NOT NULL
                  AND c.cohort_hash <> ''
                  AND NOT EXISTS (
                    SELECT 1
                    FROM vertex_natural_person_latent_materialization_cursor x
                    WHERE x.cohort_hash = c.cohort_hash
                  )
                """
            )
            cursors_inserted = cur.rowcount or 0

            cur.execute(
                f"""
                UPDATE vertex_natural_person_latent_materialization_cursor
                SET batch_size = {int(BATCH_SIZE)}
                WHERE status = 'active'
                  AND batch_size IS DISTINCT FROM {int(BATCH_SIZE)}
                """
            )
            cur.execute("FLUSH")

            for _ in range(BATCHES_PER_RUN):
                cur.execute(
                    f"""
                    INSERT INTO vertex_latent_entity (
                      vertex_id, _seq, sensitivity_ord, owner_did, actor_did, org_did,
                      created_at, entity_kind, canonical_label, existence_probability,
                      k_evidence_count, viewpoint_consensus, fission_eligible, status,
                      primary_topic_vid, individual_did
                    )
                    SELECT
                      'at://did:web:coverage.etzhayyim.com/com.etzhayyim.apps.coverage.latentEntity/natural-person-individual-'
                        || w.cohort_hash || '-' || LPAD(g.i::VARCHAR, 12, '0'),
                      g.i,
                      300,
                      'did:web:coverage.etzhayyim.com',
                      'did:web:coverage.etzhayyim.com',
                      'did:web:coverage.etzhayyim.com',
                      NOW(),
                      'natural_person_individual_latent',
                      'natural person latent: ' || w.cohort_hash || ' #' || g.i::VARCHAR,
                      0.50,
                      1,
                      1,
                      false,
                      'active',
                      w.cohort_vid,
                      'did:web:natural-person.etzhayyim.com:latent:' || w.cohort_hash || ':' || g.i::VARCHAR
                    FROM (
                      SELECT
                        vertex_id,
                        cohort_vid,
                        cohort_hash,
                        target_count,
                        next_ordinal,
                        LEAST(next_ordinal + {int(BATCH_SIZE)} - 1, target_count) AS end_ordinal
                      FROM vertex_natural_person_latent_materialization_cursor
                      WHERE status = 'active'
                        AND next_ordinal <= target_count
                      ORDER BY updated_at ASC NULLS FIRST, cohort_hash
                      LIMIT 1
                    ) w,
                    generate_series(w.next_ordinal, w.end_ordinal) AS g(i)
                    """
                )
                inserted = cur.rowcount or 0
                total_inserted += inserted

                if inserted <= 0:
                    break

                cur.execute(
                    """
                    UPDATE vertex_natural_person_latent_materialization_cursor
                    SET
                      next_ordinal = LEAST(target_count + 1, next_ordinal + batch_size),
                      materialized_count = LEAST(target_count, materialized_count + batch_size),
                      status = CASE
                        WHEN next_ordinal + batch_size > target_count THEN 'complete'
                        ELSE 'active'
                      END,
                      updated_at = NOW()
                    WHERE vertex_id = (
                      SELECT vertex_id
                      FROM vertex_natural_person_latent_materialization_cursor
                      WHERE status = 'active'
                        AND next_ordinal <= target_count
                      ORDER BY updated_at ASC NULLS FIRST, cohort_hash
                      LIMIT 1
                    )
                    """
                )
                advanced = cur.rowcount or 0
                total_advanced += advanced

            cur.execute(
                """
                SELECT
                  COALESCE(SUM(materialized_count), 0)::bigint AS materialized,
                  COALESCE(SUM(target_count), 0)::bigint AS target,
                  COALESCE(SUM(GREATEST(target_count - next_ordinal + 1, 0)), 0)::bigint AS remaining,
                  SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END)::bigint AS active_cursors,
                  SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END)::bigint AS complete_cursors
                FROM vertex_natural_person_latent_materialization_cursor
                """
            )
            row = cur.fetchone()

    materialized, target, remaining, active_cursors, complete_cursors = row or (0, 0, 0, 0, 0)
    elapsed_ms = int((time.time() - started) * 1000)
    print(
        "natural-person-materialize-all-latent-entities "
        f"cursorsInserted={cursors_inserted} inserted={total_inserted} "
        f"advanced={total_advanced} materialized={materialized} target={target} "
        f"remaining={remaining} activeCursors={active_cursors} "
        f"completeCursors={complete_cursors} elapsedMs={elapsed_ms}"
    )


if __name__ == "__main__":
    main()
