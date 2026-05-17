"""Open3D mesh post-processing for maps3d.

Quadric-decimates a COLMAP `meshed.ply` (typically 50-300 K triangles)
to a target count (default 5 K) and exports as a vertex-colored GLB.
Per-vertex colors are saturated by `saturate` (default 1.3) and
clipped to [0, 1] so simplified tiles read as Nintendo-style cel
shading rather than blurred photoreal.

Open3D's GLB writer requires `write_vertex_colors=True` and writes
COLOR_0 as VEC3 RGB float32 — exactly what `MeshTileAdapter` expects.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("maps3d.mesh")


def simplify_to_glb(
    in_ply: Path,
    out_glb: Path,
    *,
    target_triangles: int = 5000,
    saturate: float = 1.3,
) -> tuple[int, int]:
    """Decimate `in_ply` → vertex-colored `out_glb`. Returns
    (triangle_count, byte_size)."""
    import numpy as np
    import open3d as o3d

    if not in_ply.exists():
        raise FileNotFoundError(in_ply)

    mesh = o3d.io.read_triangle_mesh(str(in_ply))
    if not mesh.has_vertices() or not mesh.has_triangles():
        raise ValueError(f"empty mesh: {in_ply}")

    # Quadric edge-collapse decimation. Open3D returns a fresh mesh.
    if len(mesh.triangles) > target_triangles:
        mesh = mesh.simplify_quadric_decimation(
            target_number_of_triangles=target_triangles
        )

    if not mesh.has_vertex_normals():
        mesh.compute_vertex_normals()

    # Saturation boost on vertex colors. COLMAP outputs RGB in [0,1]
    # already; some decimation paths drop colors so guard.
    if mesh.has_vertex_colors():
        v = np.asarray(mesh.vertex_colors)
        v = np.clip(v * float(saturate), 0.0, 1.0)
        mesh.vertex_colors = o3d.utility.Vector3dVector(v)
    else:
        # Fall back to a stone-warm grey so the GLB still has COLOR_0.
        n = len(mesh.vertices)
        mesh.vertex_colors = o3d.utility.Vector3dVector(
            np.tile(np.array([0.78, 0.74, 0.69], dtype=float), (n, 1))
        )

    out_glb.parent.mkdir(parents=True, exist_ok=True)
    ok = o3d.io.write_triangle_mesh(
        str(out_glb),
        mesh,
        write_vertex_colors=True,
        write_vertex_normals=True,
        compressed=False,
    )
    if not ok:
        raise RuntimeError(f"open3d failed to write {out_glb}")

    tri_count = len(mesh.triangles)
    byte_size = out_glb.stat().st_size
    log.info(
        "simplify %s → %s · %d tris · %d B",
        in_ply.name,
        out_glb.name,
        tri_count,
        byte_size,
    )
    return tri_count, byte_size
