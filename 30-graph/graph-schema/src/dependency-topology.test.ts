import { describe, expect, it } from "vitest";
import { computeDependencyTopologyOrder } from "./dependency-topology.js";

describe("computeDependencyTopologyOrder", () => {
  it("sorts prerequisites before dependents and exposes reverse topo rank", () => {
    const rows = computeDependencyTopologyOrder(
      [
        { vertexId: "deploy", displayName: "Deploy" },
        { vertexId: "build", displayName: "Build" },
        { vertexId: "schema", displayName: "Schema" },
      ],
      [
        { dependentVid: "deploy", prerequisiteVid: "build" },
        { dependentVid: "build", prerequisiteVid: "schema" },
      ],
      { computedAt: "2026-04-29T20:30:00+09:00" },
    );

    expect(rows.map((row) => row.vertex_id)).toEqual(["schema", "build", "deploy"]);
    expect(rows.map((row) => row.reverse_topo_rank)).toEqual([2, 1, 0]);
    expect(rows.find((row) => row.vertex_id === "deploy")?.dependency_count).toBe(1);
    expect(rows.find((row) => row.vertex_id === "schema")?.dependent_count).toBe(1);
  });

  it("marks cycle members without dropping them", () => {
    const rows = computeDependencyTopologyOrder(
      [{ vertexId: "a" }, { vertexId: "b" }],
      [
        { dependentVid: "a", prerequisiteVid: "b" },
        { dependentVid: "b", prerequisiteVid: "a" },
      ],
    );

    expect(rows).toHaveLength(2);
    expect(rows.every((row) => row.cycle_status === "cycle_member")).toBe(true);
  });

  it("counts unresolved prerequisites against the explicit node set", () => {
    const rows = computeDependencyTopologyOrder(
      [{ vertexId: "deploy" }],
      [{ dependentVid: "deploy", prerequisiteVid: "missing-build" }],
    );

    expect(rows.find((row) => row.vertex_id === "deploy")?.unresolved_dependency_count).toBe(1);
    expect(rows.find((row) => row.vertex_id === "missing-build")?.cycle_status).toBe("acyclic");
  });
});
