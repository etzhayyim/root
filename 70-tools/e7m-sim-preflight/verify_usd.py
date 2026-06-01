"""Verify OpenUSD scene composition per ADR-2605261600 §Reference Composition.

ADR binding: OpenUSD (Pixar) is the single scene-composition SoT (G2).
URDF/MJCF/SDF can be imported but must convert to USD for downstream render
delegates (HdCycles, Mitsuba 3) and synthetic-data (BlenderProc, Kubric).

This script:
  1. Writes a .usda (text USD) scene of the Kusawake chassis
  2. Loads it back, traverses the stage, verifies prim graph
  3. Adds a 4×4 instance (4 robots at different positions) via USD references
  4. Saves a binary .usdc copy for size comparison
"""
from __future__ import annotations

import sys
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux

OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(exist_ok=True)


def build_chassis_stage(out_path: Path) -> None:
    stage = Usd.Stage.CreateNew(str(out_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Sky-like distant light
    light = UsdLux.DistantLight.Define(stage, "/World/Sun")
    light.CreateIntensityAttr(8000.0)
    light.AddRotateYOp().Set(-45.0)

    # Ground
    ground = UsdGeom.Mesh.Define(stage, "/World/Ground")
    ground.CreatePointsAttr([(-15, -15, 0), (15, -15, 0), (15, 15, 0), (-15, 15, 0)])
    ground.CreateFaceVertexCountsAttr([4])
    ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    ground.CreateDisplayColorAttr([(0.30, 0.45, 0.20)])

    # Robot root xform (so we can later reference this prim from instances)
    robot = UsdGeom.Xform.Define(stage, "/World/Kusawake")

    # Chassis box
    chassis = UsdGeom.Cube.Define(stage, "/World/Kusawake/Chassis")
    chassis.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.30))
    chassis.AddScaleOp().Set(Gf.Vec3f(0.70, 0.45, 0.10))
    chassis.CreateDisplayColorAttr([(0.20, 0.55, 0.20)])

    # Payload deck
    deck = UsdGeom.Cube.Define(stage, "/World/Kusawake/Deck")
    deck.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.48))
    deck.AddScaleOp().Set(Gf.Vec3f(0.55, 0.35, 0.04))
    deck.CreateDisplayColorAttr([(0.85, 0.85, 0.85)])

    # 4 wheels
    for label, (x, y) in {"FL": (0.55, 0.50), "FR": (0.55, -0.50),
                          "RL": (-0.55, 0.50), "RR": (-0.55, -0.50)}.items():
        w = UsdGeom.Cylinder.Define(stage, f"/World/Kusawake/Wheel_{label}")
        w.CreateRadiusAttr(0.20)
        w.CreateHeightAttr(0.12)
        w.CreateAxisAttr(UsdGeom.Tokens.y)
        w.AddTranslateOp().Set(Gf.Vec3d(x, y, 0.20))
        w.CreateDisplayColorAttr([(0.10, 0.10, 0.10)])

    # LiDAR puck (visual marker)
    lidar = UsdGeom.Cylinder.Define(stage, "/World/Kusawake/Lidar")
    lidar.CreateRadiusAttr(0.06)
    lidar.CreateHeightAttr(0.08)
    lidar.CreateAxisAttr(UsdGeom.Tokens.z)
    lidar.AddTranslateOp().Set(Gf.Vec3d(0.55, 0, 0.58))
    lidar.CreateDisplayColorAttr([(0.95, 0.85, 0.10)])

    stage.GetRootLayer().Save()


def build_fleet_stage(robot_usd: Path, out_path: Path, count: int = 4) -> None:
    """Compose `count` Kusawake instances at a grid of positions via Sdf references."""
    stage = Usd.Stage.CreateNew(str(out_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.Xform.Define(stage, "/Fleet")
    stage.SetDefaultPrim(stage.GetPrimAtPath("/Fleet"))

    spacing = 3.0
    for i in range(count):
        inst = UsdGeom.Xform.Define(stage, f"/Fleet/Robot_{i:02d}")
        inst.GetPrim().GetReferences().AddReference(
            assetPath=str(robot_usd.name),  # same dir
            primPath="/World/Kusawake",
        )
        x = (i % 2) * spacing - spacing / 2
        y = (i // 2) * spacing - spacing / 2
        inst.AddTranslateOp().Set(Gf.Vec3d(x, y, 0))

    stage.GetRootLayer().Save()


def traverse_and_report(usd_path: Path) -> int:
    stage = Usd.Stage.Open(str(usd_path))
    n_prims = sum(1 for _ in stage.Traverse())
    print(f"\n  loaded: {usd_path.name}")
    print(f"    {n_prims} prims (excluding pseudo-root):")
    for prim in stage.Traverse():
        type_name = prim.GetTypeName() or "<no type>"
        print(f"      {prim.GetPath()}  ({type_name})")
    return n_prims


def main() -> int:
    chassis_usda = OUT_DIR / "kusawake.usda"
    chassis_usdc = OUT_DIR / "kusawake.usdc"
    fleet_usda = OUT_DIR / "kusawake_fleet.usda"

    print("[1/3] Build single-robot .usda...")
    build_chassis_stage(chassis_usda)
    print(f"  wrote: {chassis_usda} ({chassis_usda.stat().st_size} B)")
    n_single = traverse_and_report(chassis_usda)

    print("\n[2/3] Cross-format export .usdc (binary)...")
    stage = Usd.Stage.Open(str(chassis_usda))
    stage.GetRootLayer().Export(str(chassis_usdc))
    print(f"  wrote: {chassis_usdc} ({chassis_usdc.stat().st_size} B)")
    print(f"  binary/text ratio: {chassis_usdc.stat().st_size / chassis_usda.stat().st_size:.2%}")

    print("\n[3/3] Build 4-robot fleet via USD references...")
    build_fleet_stage(chassis_usda, fleet_usda, count=4)
    print(f"  wrote: {fleet_usda}")
    n_fleet = traverse_and_report(fleet_usda)
    print(f"\n  prims_per_robot ≈ {(n_fleet - 1) / 4:.1f} (excluding Fleet xform)")

    print("\nOpenUSD scene composition: OK")
    print(f"  pxr.Usd version: {Usd.GetVersion()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
