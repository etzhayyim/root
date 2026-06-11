"""moderngl-based headless 4-view mesh renderer (works on macOS Apple Silicon via CGL/Metal)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import moderngl
import numpy as np
import trimesh
from PIL import Image

_VSHADER = """
#version 330
in vec3 in_pos;
in vec3 in_normal;
uniform mat4 mvp;
uniform mat4 model;
out vec3 v_normal;
out vec3 v_world;
void main() {
    v_normal = mat3(transpose(inverse(model))) * in_normal;
    v_world  = (model * vec4(in_pos, 1.0)).xyz;
    gl_Position = mvp * vec4(in_pos, 1.0);
}
"""

_FSHADER = """
#version 330
in vec3 v_normal;
in vec3 v_world;
uniform vec3 light_dir;
uniform vec3 view_pos;
out vec4 frag;
void main() {
    vec3 N = normalize(v_normal);
    vec3 L = normalize(light_dir);
    vec3 V = normalize(view_pos - v_world);
    vec3 H = normalize(L + V);
    float ambient = 0.25;
    float diffuse = max(dot(N, L), 0.0) * 0.7;
    float spec    = pow(max(dot(N, H), 0.0), 32.0) * 0.25;
    vec3  base    = vec3(0.85, 0.85, 0.88);
    vec3  col     = base * (ambient + diffuse) + vec3(1.0) * spec;
    frag = vec4(col, 1.0);
}
"""


def _look_at(eye, center=(0, 0, 0), up=(0, 1, 0)) -> np.ndarray:
    eye = np.asarray(eye, dtype=np.float32)
    center = np.asarray(center, dtype=np.float32)
    up = np.asarray(up, dtype=np.float32)
    f = center - eye
    f /= np.linalg.norm(f)
    s = np.cross(f, up)
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    M = np.eye(4, dtype=np.float32)
    M[0, :3] = s
    M[1, :3] = u
    M[2, :3] = -f
    M[:3, 3] = -M[:3, :3] @ eye
    return M


def _perspective(fovy: float, aspect: float, znear: float, zfar: float) -> np.ndarray:
    f = 1.0 / math.tan(fovy / 2.0)
    M = np.zeros((4, 4), dtype=np.float32)
    M[0, 0] = f / aspect
    M[1, 1] = f
    M[2, 2] = (zfar + znear) / (znear - zfar)
    M[2, 3] = 2 * zfar * znear / (znear - zfar)
    M[3, 2] = -1.0
    return M


VIEWS = [
    ("front", (0.0, 0.2, 2.2)),
    ("right", (2.2, 0.2, 0.0)),
    ("back", (0.0, 0.2, -2.2)),
    ("left", (-2.2, 0.2, 0.0)),
]


def render_4view(mesh_path: Path, out_dir: Path, prefix: str, size: int = 512) -> tuple[dict[str, str], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    mesh = trimesh.load(str(mesh_path), force="mesh")
    centroid = mesh.bounding_box.centroid
    mesh.apply_translation(-centroid)
    mesh.apply_scale(1.0 / max(mesh.extents))
    if mesh.vertex_normals is None or len(mesh.vertex_normals) == 0:
        mesh.fix_normals()
    verts = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
    norms = np.ascontiguousarray(mesh.vertex_normals, dtype=np.float32)
    faces = np.ascontiguousarray(mesh.faces, dtype=np.uint32)

    ctx = moderngl.create_standalone_context(require=330)
    prog = ctx.program(vertex_shader=_VSHADER, fragment_shader=_FSHADER)
    inter = np.empty((verts.shape[0], 6), dtype=np.float32)
    inter[:, :3] = verts
    inter[:, 3:] = norms
    vbo = ctx.buffer(inter.tobytes())
    ibo = ctx.buffer(faces.tobytes())
    vao = ctx.vertex_array(
        prog,
        [(vbo, "3f 3f", "in_pos", "in_normal")],
        index_buffer=ibo,
        index_element_size=4,
    )
    color = ctx.texture((size, size), 4)
    depth = ctx.depth_renderbuffer((size, size))
    fbo = ctx.framebuffer(color_attachments=[color], depth_attachment=depth)
    fbo.use()
    ctx.enable(moderngl.DEPTH_TEST)
    ctx.enable(moderngl.CULL_FACE)
    proj = _perspective(math.radians(40.0), 1.0, 0.1, 10.0)
    model = np.eye(4, dtype=np.float32)
    prog["model"].write(model.T.tobytes())
    prog["light_dir"].value = (1.0, 1.0, 1.0)

    paths: dict[str, str] = {}
    for name, eye in VIEWS:
        view = _look_at(eye)
        mvp = proj @ view @ model
        prog["mvp"].write(mvp.T.tobytes())
        prog["view_pos"].value = tuple(eye)
        ctx.clear(1.0, 1.0, 1.0, 1.0)
        vao.render()
        rgba = fbo.read(components=4)
        img = Image.frombytes("RGBA", (size, size), rgba).transpose(Image.FLIP_TOP_BOTTOM)
        out = out_dir / f"{prefix}_{name}.png"
        img.save(out)
        paths[name] = str(out)

    tile = Image.new("RGB", (size * 2, size * 2), (255, 255, 255))
    pos_map = {"front": (0, 0), "right": (size, 0), "back": (0, size), "left": (size, size)}
    for n, p in pos_map.items():
        im = Image.open(paths[n]).convert("RGB").resize((size, size))
        tile.paste(im, p)
    tile_path = out_dir / f"{prefix}_4view_tile.png"
    tile.save(tile_path)
    paths["tile"] = str(tile_path)

    fbo.release()
    color.release()
    depth.release()
    vao.release()
    vbo.release()
    ibo.release()
    prog.release()
    ctx.release()

    stats = {
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
        "bbox_extents": [float(x) for x in mesh.extents],
        "surface_area": float(mesh.area),
        "volume": float(mesh.volume) if mesh.is_volume else None,
        "is_watertight": bool(mesh.is_watertight),
        "is_volume": bool(mesh.is_volume),
    }
    return paths, stats
