"""suji (筋) ↔ kami-genesis / Isaac-Sim articulation bridge. Stdlib only. ADR-2606061200.

Maps the suji sagittal segment chain to the articulation spec that a kami-genesis
`PlanarChain` (Featherstone RNEA/CRBA, ADR-2605311500/1800) — exposed through the
nv-compat Isaac-Sim `ArticulationView` / `ArticulationBatch` surface (ADR-2606010030)
— would load. The data contract here is the WIT in `wit/kami-biomech.wit`.

Two functions:
  - `to_articulation(body, posture)` builds the link/joint/gravity spec (the thing you
    hand to `isaacsim.core.api` `Articulation` or kami-genesis `PlanarChain::from_spec`).
  - `solve_static(spec)` returns the per-joint gravity moments — the SAME quantity a
    kami-genesis backend returns from its full RNEA, computed here via the closed-form
    statics in `load.py` so the contract is exercised without the (unpopulated) submodule.

HONEST INTEGRATION STATE (G7): the kami-genesis Rust crate is absent in this checkout;
this is the WIT contract + reference behaviour, not a compiled backend (noroshi pattern).
NO live actuation (the body model is passive; a powered exosuit/robot driven from these
moments would be a different actor under the tazuna force-class + Council gate).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from load import solve_posture_loads
from segment import GRAVITY, BodyModel


@dataclass(frozen=True)
class KamiLink:
    name: str
    mass_kg: float
    length_m: float
    com_frac: float


@dataclass(frozen=True)
class KamiJoint:
    name: str
    parent_link: str
    child_link: str
    angle_deg: float


@dataclass(frozen=True)
class KamiArticulation:
    links: list[KamiLink]
    joints: list[KamiJoint]
    gravity_mps2: float

    def to_dict(self) -> dict:
        return {
            "links": [asdict(l) for l in self.links],
            "joints": [asdict(j) for j in self.joints],
            "gravity_mps2": self.gravity_mps2,
        }


# The sagittal kinematic order: pelvis(base) → lumbar → thorax → cervical → head, plus
# the upper-limb branch thorax → shoulder → upper_arm → elbow → forearm → wrist → hand.
_CHAIN_JOINTS = [
    ("lumbosacral", "pelvis", "thorax_abdomen", "trunk_flexion_deg"),
    ("cervicothoracic", "thorax_abdomen", "head_neck", "head_flexion_deg"),
    ("shoulder", "thorax_abdomen", "upper_arm", "shoulder_flexion_deg"),
    ("elbow", "upper_arm", "forearm", "elbow_flexion_deg"),
]


def to_articulation(body: BodyModel, posture) -> KamiArticulation:
    """Build the kami-genesis / Isaac articulation spec for a posed body."""
    links = [
        KamiLink(s.name, round(s.mass_kg, 4), round(s.length_m, 4), s.com_frac)
        for s in body.segments.values()
    ]
    # pelvis is the base link (seat support); thorax connects above it.
    angles = {
        "trunk_flexion_deg": posture.trunk_flexion_deg,
        "head_flexion_deg": posture.head_flexion_deg,
        "shoulder_flexion_deg": posture.shoulder_flexion_deg,
        "elbow_flexion_deg": posture.elbow_flexion_deg,
    }
    joints = [
        KamiJoint(name, parent, child, angles[ang_key])
        for (name, parent, child, ang_key) in _CHAIN_JOINTS
    ]
    return KamiArticulation(links=links, joints=joints, gravity_mps2=GRAVITY)


def solve_static(body: BodyModel, posture) -> list[dict]:
    """Per-joint static gravity moments — the quantity a kami-genesis RNEA returns.

    Reference implementation via the closed-form statics (load.py). A live backend
    would instead call kami-genesis `PlanarChain::inverse_dynamics` with zero velocity
    and acceleration (the gravity term).
    """
    loads = solve_posture_loads(body, posture)
    out = [{"joint": "cervicothoracic", "moment_nm": round(loads.cervical.extensor_moment_nm, 4)}]
    for j in loads.joints:
        if j.joint == "cervicothoracic":
            continue
        out.append({"joint": j.joint, "moment_nm": round(j.moment_nm, 4)})
    return out
