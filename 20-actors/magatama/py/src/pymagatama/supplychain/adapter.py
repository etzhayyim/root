"""Domain adapters for supplychain.etzhayyim.com — cleaning robot manufacturing.

Normalizes robotics and automotive material tables into the shared
jukyu SoS tables (domain='cleaning_robot') so the Pregel graph can run
the same pressure-propagation algorithm across the cleaning robot
upstream material graph.
"""

from __future__ import annotations

from typing import Any

from pymagatama.db_sync import execute


def normalize_cleaning_robot() -> dict[str, Any]:
    """Normalize the cleaning-robot manufacturing supply graph into Jukyu SoS tables.

    Sources:
      vertex_automotive_material_requirement  → material supply nodes
      vertex_robotics_product_package         → assembly nodes
      edge_automotive_material_supplied_by    → supplier nodes + supplier→material edges
      edge_automotive_package_requires_material → material→package edges

    Idempotent: all cleaning_robot rows are deleted before re-insert.
    """
    stats: dict[str, Any] = {"ok": True, "domain": "cleaning_robot"}

    # ── Idempotent deletes ────────────────────────────────────────────────────
    execute(
        "DELETE FROM edge_jukyu_company_operates_node WHERE edge_id LIKE %s",
        ("jukyu-operates:cleaning_robot:%",),
    )
    execute(
        "DELETE FROM edge_jukyu_supply_dependency WHERE edge_id LIKE %s",
        ("jukyu-edge:cleaning_robot:%",),
    )
    execute(
        "DELETE FROM vertex_jukyu_company_exposure WHERE run_id = %s",
        ("jukyu.adapter.cleaning_robot.latest",),
    )
    execute(
        "DELETE FROM vertex_jukyu_balance_observation WHERE source_kind = %s",
        ("cleaning_robot_adapter",),
    )
    execute(
        "DELETE FROM vertex_jukyu_supply_node WHERE source_table = %s",
        ("vertex_automotive_material_requirement",),
    )
    execute(
        "DELETE FROM vertex_jukyu_supply_node WHERE source_table = %s",
        ("vertex_robotics_product_package",),
    )
    execute(
        "DELETE FROM vertex_jukyu_supply_node WHERE source_table = %s",
        ("edge_automotive_material_supplied_by",),
    )

    # ── Supply nodes: material requirements ──────────────────────────────────
    stats["materialNodes"] = execute(
        """
        INSERT INTO vertex_jukyu_supply_node
          (vertex_id, created_date, sensitivity_ord, owner_did, repo,
           domain, node_code, node_kind, display_name, country_code,
           operator_did, product_code, product_family, capacity_unit,
           demand_capacity, status, source_table, source_vertex_id,
           collection, actor_did, org_did)
        SELECT
          'jukyu-node:cleaning_robot:material:' || vertex_id,
          CURRENT_DATE,
          COALESCE(sensitivity_ord, 1),
          COALESCE(owner_did, 'did:web:supplychain.etzhayyim.com'),
          COALESCE(repo, 'did:web:supplychain.etzhayyim.com'),
          'cleaning_robot',
          material_id,
          COALESCE(material_kind, 'material'),
          COALESCE(specification, material_id),
          COALESCE(country_of_origin, 'ZZ'),
          NULL,
          COALESCE(material_kind, 'cleaning_robot_material'),
          'cleaning_robot_material',
          'units',
          COALESCE(quantity_per_vehicle, 1.0),
          COALESCE(status, 'active'),
          'vertex_automotive_material_requirement',
          vertex_id,
          'app.etzhayyim.apps.supplychain.supplyNode',
          'did:web:supplychain.etzhayyim.com',
          'did:web:etzhayyim.com'
        FROM vertex_automotive_material_requirement
        WHERE status IS NULL OR status <> 'deleted'
        """
    )

    # ── Supply nodes: robotics product packages (assembly nodes) ─────────────
    stats["assemblyNodes"] = execute(
        """
        INSERT INTO vertex_jukyu_supply_node
          (vertex_id, created_date, sensitivity_ord, owner_did, repo,
           domain, node_code, node_kind, display_name, country_code,
           operator_did, product_code, product_family, capacity_unit,
           status, source_table, source_vertex_id,
           collection, actor_did, org_did)
        SELECT
          'jukyu-node:cleaning_robot:package:' || vertex_id,
          CURRENT_DATE,
          COALESCE(sensitivity_ord, 1),
          COALESCE(owner_did, 'did:web:supplychain.etzhayyim.com'),
          COALESCE(repo, 'did:web:supplychain.etzhayyim.com'),
          'cleaning_robot',
          package_id,
          COALESCE(asset_kind, 'assembly'),
          COALESCE(package_id, vertex_id),
          COALESCE(target_supplier_region, 'JP'),
          NULL,
          COALESCE(asset_kind, 'cleaning_robot'),
          'cleaning_robot_assembly',
          'units',
          COALESCE(readiness_status, 'active'),
          'vertex_robotics_product_package',
          vertex_id,
          'app.etzhayyim.apps.supplychain.supplyNode',
          'did:web:supplychain.etzhayyim.com',
          'did:web:etzhayyim.com'
        FROM vertex_robotics_product_package
        WHERE readiness_status IS NULL OR readiness_status <> 'cancelled'
        """
    )

    # ── Supply nodes: unique suppliers (from edge_automotive_material_supplied_by) ──
    # One node per supplier_lei; CTE avoids DISTINCT ON (RisingWave-safe).
    stats["supplierNodes"] = execute(
        """
        WITH unique_suppliers AS (
          SELECT
            supplier_lei,
            MIN(edge_id)          AS edge_id,
            MAX(CASE WHEN qualification_status = 'qualified' THEN 1 ELSE 0 END)
                                  AS is_qualified
          FROM edge_automotive_material_supplied_by
          WHERE supplier_lei IS NOT NULL
          GROUP BY supplier_lei
        )
        INSERT INTO vertex_jukyu_supply_node
          (vertex_id, created_date, sensitivity_ord, owner_did, repo,
           domain, node_code, node_kind, display_name, country_code,
           operator_did, product_code, product_family, capacity_unit,
           status, source_table, source_vertex_id,
           collection, actor_did, org_did)
        SELECT
          'jukyu-node:cleaning_robot:supplier:' || s.supplier_lei,
          CURRENT_DATE,
          1,
          'did:web:supplychain.etzhayyim.com',
          'did:web:supplychain.etzhayyim.com',
          'cleaning_robot',
          s.supplier_lei,
          'supplier',
          s.supplier_lei,
          'ZZ',
          'did:web:lei:' || s.supplier_lei,
          'cleaning_robot_material',
          'cleaning_robot_supplier',
          'units',
          CASE s.is_qualified WHEN 1 THEN 'active' ELSE 'inactive' END,
          'edge_automotive_material_supplied_by',
          s.edge_id,
          'app.etzhayyim.apps.supplychain.supplyNode',
          'did:web:supplychain.etzhayyim.com',
          'did:web:etzhayyim.com'
        FROM unique_suppliers s
        """
    )

    # ── Supply dependencies: supplier → material (supplier provides material) ─
    stats["supplierMaterialDeps"] = execute(
        """
        INSERT INTO edge_jukyu_supply_dependency
          (edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
           domain, relationship, product_code, product_family,
           dependency_weight, confidence, status)
        SELECT
          'jukyu-edge:cleaning_robot:supplier:' || e.edge_id,
          sup_node.vertex_id,
          mat_node.vertex_id,
          CURRENT_DATE,
          1,
          'did:web:supplychain.etzhayyim.com',
          'cleaning_robot',
          'material_supply',
          e.material_id,
          'cleaning_robot_material',
          CASE e.qualification_status
            WHEN 'qualified'    THEN 1.0
            WHEN 'conditional'  THEN 0.5
            ELSE 0.2
          END,
          0.70,
          CASE e.qualification_status
            WHEN 'disqualified' THEN 'inactive'
            ELSE 'active'
          END
        FROM edge_automotive_material_supplied_by e
        INNER JOIN vertex_jukyu_supply_node sup_node
          ON sup_node.node_code = e.supplier_lei
         AND sup_node.domain        = 'cleaning_robot'
         AND sup_node.source_table  = 'edge_automotive_material_supplied_by'
        INNER JOIN vertex_jukyu_supply_node mat_node
          ON mat_node.node_code    = e.material_id
         AND mat_node.domain       = 'cleaning_robot'
         AND mat_node.source_table = 'vertex_automotive_material_requirement'
        WHERE e.qualification_status IS NULL OR e.qualification_status <> 'disqualified'
        """
    )

    # ── Supply dependencies: material → package (package requires material) ──
    stats["packageMaterialDeps"] = execute(
        """
        INSERT INTO edge_jukyu_supply_dependency
          (edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
           domain, relationship, product_code, product_family,
           dependency_weight, confidence, status)
        SELECT
          'jukyu-edge:cleaning_robot:pkg-mat:' || e.edge_id,
          mat_node.vertex_id,
          pkg_node.vertex_id,
          CURRENT_DATE,
          1,
          'did:web:supplychain.etzhayyim.com',
          'cleaning_robot',
          'material_required',
          e.material_id,
          'cleaning_robot_material',
          CASE e.requirement_kind
            WHEN 'critical' THEN 1.0
            WHEN 'optional' THEN 0.3
            ELSE 0.7
          END,
          0.65,
          'active'
        FROM edge_automotive_package_requires_material e
        INNER JOIN vertex_jukyu_supply_node mat_node
          ON mat_node.node_code    = e.material_id
         AND mat_node.domain       = 'cleaning_robot'
         AND mat_node.source_table = 'vertex_automotive_material_requirement'
        INNER JOIN vertex_jukyu_supply_node pkg_node
          ON pkg_node.node_code    = e.package_id
         AND pkg_node.domain       = 'cleaning_robot'
         AND pkg_node.source_table = 'vertex_robotics_product_package'
        """
    )

    # ── Balance observations: demand = material req count, supply = qualified suppliers ──
    # Groups by (country_of_origin, material_kind) — bounded cardinality.
    stats["balanceObservations"] = execute(
        """
        INSERT INTO vertex_jukyu_balance_observation
          (vertex_id, created_date, sensitivity_ord, owner_did, repo,
           observation_id, domain, country_code, product_code, product_family,
           supply_quantity, demand_quantity, balance_quantity, quantity_unit,
           observed_at, source_kind, confidence, status,
           collection, actor_did, org_did)
        SELECT
          'jukyu-obs:cleaning_robot:'
            || COALESCE(m.country_of_origin, 'ZZ')
            || ':' || COALESCE(m.material_kind, 'unknown'),
          CURRENT_DATE,
          1,
          'did:web:supplychain.etzhayyim.com',
          'did:web:supplychain.etzhayyim.com',
          'cleaning_robot_adapter:'
            || COALESCE(m.country_of_origin, 'ZZ')
            || ':' || COALESCE(m.material_kind, 'unknown'),
          'cleaning_robot',
          COALESCE(m.country_of_origin, 'ZZ'),
          COALESCE(m.material_kind, 'cleaning_robot_material'),
          'cleaning_robot_material',
          CAST(COUNT(DISTINCT ms.supplier_lei) AS DOUBLE PRECISION),
          CAST(COUNT(*) AS DOUBLE PRECISION),
          CAST(COUNT(DISTINCT ms.supplier_lei) AS DOUBLE PRECISION)
            - CAST(COUNT(*) AS DOUBLE PRECISION),
          'units',
          CURRENT_TIMESTAMP::VARCHAR,
          'cleaning_robot_adapter',
          0.60,
          'active',
          'app.etzhayyim.apps.supplychain.balanceObservation',
          'did:web:supplychain.etzhayyim.com',
          'did:web:etzhayyim.com'
        FROM vertex_automotive_material_requirement m
        LEFT JOIN edge_automotive_material_supplied_by ms
          ON ms.material_id = m.material_id
         AND (ms.qualification_status IS NULL OR ms.qualification_status = 'qualified')
        WHERE m.status IS NULL OR m.status <> 'deleted'
        GROUP BY
          COALESCE(m.country_of_origin, 'ZZ'),
          COALESCE(m.material_kind, 'unknown')
        """
    )

    return stats
