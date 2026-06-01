#!/usr/bin/env python3
"""sarutahiko-factory-r0 — IFC4 (ISO-10303-21 / STEP) export.

Converts the scene SSoT into `factory.ifc` — a structurally-valid IFC4 model
openable in real BIM tooling (BlenderBIM / IfcOpenShell / FreeCAD-BIM / most IFC
viewers). Every element is a box (IfcExtrudedAreaSolid over an IfcRectangleProfile,
the same box model the kami viewer renders), wired into the spatial hierarchy
IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey, and tagged with a
property set carrying 企業名 / 機器名 / 調達もと from `building.edn`.

HONEST SCOPE: box-level geometry (no detailed profiles/connections), single
storey, no IfcRelConnects topology, no structural/MEP system objects beyond
IfcFlowSegment placeholders. It is a real, importable IFC handoff of THIS model —
not a substitute for a modelled BIM authored in Revit/Archicad by an engineer.

`export_ifc(scene, parts, path)`.
"""
import hashlib
import json
import sys
from pathlib import Path


_GUID_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"


def ifc_guid(key):
    """Deterministic 22-char IFC GUID from a stable key."""
    num = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)
    digits = []
    n = num
    for _ in range(21):
        digits.append(n & 63)
        n >>= 6
    digits.append(n & 3)
    digits.reverse()
    return "".join(_GUID_CHARS[d] for d in digits)


class Ifc:
    """Tiny STEP writer with an incrementing #id counter."""

    def __init__(self):
        self.lines = []
        self.n = 0

    def add(self, body):
        self.n += 1
        self.lines.append(f"#{self.n}={body};")
        return self.n

    def ref(self, i):
        return f"#{i}"

    def reflist(self, ids):
        return "(" + ",".join(f"#{i}" for i in ids) + ")"


def _aabb_box(a):
    return (0.5 * (a[0] + a[2]), 0.5 * (a[1] + a[3]),
            max(a[2] - a[0], 0.05), max(a[3] - a[1], 0.05))


def export_ifc(scene, parts, path):
    f = Ifc()
    # link a BOM part to a render-element id via :part/sim-feature
    by_feat = {}
    for p in parts:
        sf = p.get("part/sim-feature")
        if sf and sf not in by_feat:
            by_feat[sf] = p

    # ── shared geometry context ──
    org = f.add("IFCORGANIZATION($,'etzhayyim','Sarutahiko factory R0 (kami-engine)',$,$)")
    person = f.add("IFCPERSON($,'kami-app-sarutahiko-factory',$,$,$,$,$,$)")
    pando = f.add(f"IFCPERSONANDORGANIZATION(#{person},#{org},$)")
    app = f.add(f"IFCAPPLICATION(#{org},'R0','kotoba-sarutahiko-factory','sarutahiko-factory')")
    owner = f.add(f"IFCOWNERHISTORY(#{pando},#{app},$,.ADDED.,$,$,$,0)")

    p0 = f.add("IFCCARTESIANPOINT((0.,0.,0.))")
    dz = f.add("IFCDIRECTION((0.,0.,1.))")
    dx = f.add("IFCDIRECTION((1.,0.,0.))")
    axis3 = f.add(f"IFCAXIS2PLACEMENT3D(#{p0},#{dz},#{dx})")
    wcs = f.add(f"IFCAXIS2PLACEMENT3D(#{p0},#{dz},#{dx})")
    ctx = f.add(f"IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#{wcs},$)")

    lu = f.add("IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)")
    au = f.add("IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.)")
    vu = f.add("IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.)")
    pa = f.add("IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.)")
    units = f.add(f"IFCUNITASSIGNMENT((#{lu},#{au},#{vu},#{pa}))")

    proj = f.add(f"IFCPROJECT('{ifc_guid('project')}',#{owner},'sarutahiko-factory-r0',"
                 f"'Sarutahiko robot manufacturing plant R0',$,$,$,(#{ctx}),#{units})")

    # ── spatial hierarchy ──
    def placement(parent_id, x, y, z):
        pt = f.add(f"IFCCARTESIANPOINT(({x:.4f},{y:.4f},{z:.4f}))")
        a3 = f.add(f"IFCAXIS2PLACEMENT3D(#{pt},#{dz},#{dx})")
        if parent_id is None:
            return f.add(f"IFCLOCALPLACEMENT($,#{a3})")
        return f.add(f"IFCLOCALPLACEMENT(#{parent_id},#{a3})")

    site_pl = placement(None, 0.0, 0.0, 0.0)
    site = f.add(f"IFCSITE('{ifc_guid('site')}',#{owner},'Site',$,$,#{site_pl},$,$,"
                 f".ELEMENT.,$,$,$,$,$)")
    bldg_pl = placement(site_pl, 0.0, 0.0, 0.0)
    bldg = f.add(f"IFCBUILDING('{ifc_guid('bldg')}',#{owner},'Plant',$,$,#{bldg_pl},$,$,"
                 f".ELEMENT.,$,$,$)")
    storey_pl = placement(bldg_pl, 0.0, 0.0, 0.0)
    storey = f.add(f"IFCBUILDINGSTOREY('{ifc_guid('storey')}',#{owner},'GF',$,$,#{storey_pl},"
                   f"$,$,.ELEMENT.,0.)")

    f.add(f"IFCRELAGGREGATES('{ifc_guid('agg-proj')}',#{owner},$,$,#{proj},(#{site}))")
    f.add(f"IFCRELAGGREGATES('{ifc_guid('agg-site')}',#{owner},$,$,#{site},(#{bldg}))")
    f.add(f"IFCRELAGGREGATES('{ifc_guid('agg-bldg')}',#{owner},$,$,#{bldg},(#{storey}))")

    contained = []  # element ids placed in the storey
    rel_psets = []

    def box_element(ifc_class, eid, name, cx, cy, cz, sx, sy, sz):
        # extruded rectangle (sx x sy) by sz, base at cz - sz/2.
        # All classes use the IFC4 9-attribute element pattern with PredefinedType=$
        # (optional) so the file stays schema-valid without per-class attr bookkeeping.
        prof_pos = f.add(f"IFCAXIS2PLACEMENT2D(#{f.add('IFCCARTESIANPOINT((0.,0.))')},"
                         f"#{f.add('IFCDIRECTION((1.,0.))')})")
        prof = f.add(f"IFCRECTANGLEPROFILEDEF(.AREA.,$,#{prof_pos},{sx:.4f},{sy:.4f})")
        solid = f.add(f"IFCEXTRUDEDAREASOLID(#{prof},#{axis3},#{dz},{sz:.4f})")
        shape = f.add(f"IFCSHAPEREPRESENTATION(#{ctx},'Body','SweptSolid',(#{solid}))")
        pds = f.add(f"IFCPRODUCTDEFINITIONSHAPE($,$,(#{shape}))")
        pl = placement(storey_pl, cx, cy, cz - sz / 2.0)
        nm = name.replace("'", "")
        e = f.add(f"IFC{ifc_class}('{ifc_guid(eid)}',#{owner},'{nm}',$,$,#{pl},#{pds},'{eid}',$)")
        contained.append(e)
        # property set from the BOM (企業名/機器名/調達もと) if linked
        part = by_feat.get(eid)
        if part:
            import procurement
            proc = procurement.enrich_part(part)
            props = []
            for label, val in (
                ("企業名/Manufacturer", part.get("part/manufacturer", "")),
                ("機器名/Model", part.get("part/product", "")),
                ("型番/MPN", part.get("part/mpn", "")),
                ("調達もと/Supplier", proc.get("part/supplier", "")),
                ("原産国/Origin", proc.get("part/origin", "")),
                ("part-id", part.get("part/id", "")),
            ):
                if val:
                    sval = str(val).replace("'", "")
                    props.append(f.add(
                        f"IFCPROPERTYSINGLEVALUE('{label}',$,IFCTEXT('{sval}'),$)"))
            if props:
                ps = f.add(f"IFCPROPERTYSET('{ifc_guid('ps-' + eid)}',#{owner},"
                           f"'Pset_SarutahikoProcurement',$,{f.reflist(props)})")
                rel_psets.append((e, ps, eid))
        return e

    # structure
    for c in scene.get("columns", []):
        box_element("COLUMN", c["id"], "Column", c["x"], c["y"], c["height"] / 2,
                    c["w"], c["w"], c["height"])
    for b in scene.get("beams", []):
        y0, y1 = sorted(b["span_y"])
        box_element("BEAM", b["id"], "Roof beam", b["x"], 0.5 * (y0 + y1), b["z"],
                    b["section"], y1 - y0, b["section"])
    for w in scene.get("walls", []):
        cx, cy, sx, sy = _aabb_box(w["aabb"])
        box_element("WALL", w["id"], "Wall", cx, cy, w["height"] / 2, sx, sy, w["height"])
    # floor slab
    bb = scene["bbox_m"]
    box_element("SLAB", "floor", "Ground slab", 0.5 * (bb[0] + bb[2]), 0.5 * (bb[1] + bb[3]),
                0.0, bb[2] - bb[0], bb[3] - bb[1], 0.2)
    # zones → IfcBuildingElementProxy (kept box-uniform; IfcSpace has extra attrs)
    for z in scene.get("zones", []):
        cx, cy, sx, sy = _aabb_box(z["rect"])
        box_element("BUILDINGELEMENTPROXY", z["id"], "Zone " + z["label"], cx, cy, 0.1,
                    sx, sy, 0.2)
    # machines + service nodes → IfcBuildingElementProxy
    for m in scene.get("machines", []):
        cx, cy, sx, sy = _aabb_box(m["aabb"])
        box_element("BUILDINGELEMENTPROXY", m["id"], m["kind"], cx, cy, m["height"] / 2,
                    sx, sy, m["height"])
    for nb in scene.get("service_nodes", []):
        cx, cy, sx, sy = _aabb_box(nb["aabb"])
        box_element("BUILDINGELEMENTPROXY", nb["id"], nb["kind"], cx, cy, nb["height"] / 2,
                    sx, sy, nb["height"])
    # utilities → IfcFlowSegment (one box per polyline segment, bbox proxy)
    for u in scene.get("utilities", []):
        pts = u["path"]
        hw = max(u["width"], 0.12)
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
            sx = max(abs(x1 - x0), hw)
            sy = max(abs(y1 - y0), hw)
            box_element("FLOWSEGMENT", f"{u['id']}_{i}", u["kind"], cx, cy, u["z"],
                        sx, sy, hw)

    if contained:
        f.add(f"IFCRELCONTAINEDINSPATIALSTRUCTURE('{ifc_guid('contain')}',#{owner},$,$,"
              f"{f.reflist(contained)},#{storey})")
    for e, ps, eid in rel_psets:
        f.add(f"IFCRELDEFINESBYPROPERTIES('{ifc_guid('rdp-' + eid)}',#{owner},$,$,"
              f"(#{e}),#{ps})")

    body = "\n".join(f.lines)
    header = (
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2]'),'2;1');\n"
        "FILE_NAME('factory.ifc','2026-05-31T00:00:00',('etzhayyim'),('etzhayyim'),"
        "'kotoba-sarutahiko-factory','kami-app-sarutahiko-factory','');\n"
        "FILE_SCHEMA(('IFC4'));\n"
        "ENDSEC;\n"
        "DATA;\n"
    )
    footer = "\nENDSEC;\nEND-ISO-10303-21;\n"
    Path(path).write_text(header + body + footer, encoding="utf-8")
    return {"entities": f.n, "elements": len(contained), "psets": len(rel_psets)}


def main():
    from kotoba_gen import parse_edn
    here = Path(__file__).resolve().parent
    scene = json.loads((here / "factory.scene.json").read_text(encoding="utf-8"))
    doc = parse_edn((here / "building.edn").read_text(encoding="utf-8"))
    res = export_ifc(scene, doc["bom/parts"], here / "factory.ifc")
    print(f"wrote factory.ifc — {res['entities']} STEP entities, "
          f"{res['elements']} elements, {res['psets']} property sets")


if __name__ == "__main__":
    main()
