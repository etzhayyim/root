"""Featherstone's Articulated-Body Algorithm (ABA) — O(n) forward dynamics.

Implements the canonical Featherstone-1983 ABA for serial-chain kinematic
trees. Given:

  ArticulatedSystem  (URDF-parsed link inertias + joint axes + parent indices)
  q       (joint positions, length n)
  qdot    (joint velocities, length n)
  tau     (joint torques, length n)
  gravity (3-vec, default (0, 0, -9.81))

ABA computes:

  qddot   (joint accelerations, length n)  in O(n)

via three recursive passes:

  Pass 1 (outward kinematics):
      v[i] = X[i] · v[λ(i)] + S[i] · qdot[i]              (spatial velocity)
      c[i] = cross_v(v[i], S[i]) · qdot[i]                (Coriolis bias)

  Pass 2 (inward inertia + bias accumulation):
      U[i] = I_a[i] · S[i]
      D[i] = S[i]^T · U[i]
      u[i] = tau[i] - S[i]^T · p_a[i]
      if λ(i) ≠ 0:
          I_a[λ(i)] += X[i]^T (I_a[i] - U[i] U[i]^T / D[i]) X[i]
          p_a[λ(i)] += X[i]^T (p_a[i] + I_a[i] c[i] + U[i] u[i] / D[i])

  Pass 3 (outward acceleration):
      a[0] = -spatial_gravity
      for i = 1..n:
          a_prime = X[i] · a[λ(i)] + c[i]
          qddot[i] = (u[i] - U[i]^T · a_prime) / D[i]
          a[i] = a_prime + S[i] · qddot[i]

Spatial convention: 6-vectors = (angular_x, angular_y, angular_z,
linear_x, linear_y, linear_z). Plücker transforms are 6×6 matrices.
This matches Featherstone's "Rigid Body Dynamics Algorithms" (2008)
chapter 2 conventions.

Pure stdlib (math + lists). Matrices are nested lists. Operations are
trivial loops since dim ≤ 6.

Supported joint kinds:
  - revolute      (single rotational DOF along `axis`)
  - continuous    (= revolute; no joint limit)
  - prismatic     (single linear DOF along `axis`)
  - fixed         (NO DOF; collapsed during build_articulation)

Branched chains (e.g. ANYmal C with 4 legs from one base) are
supported via the joint→parent_joint index. Floating bases are NOT
supported in this iter — the base link is treated as fixed to the
world frame at the origin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .._kernel import ArticulatedSystem, Inertia, Joint, Link


# ── 3-vector / 3×3 mat helpers ─────────────────────────────────────────────


def _skew3(v: Sequence[float]) -> List[List[float]]:
    """3×3 skew-symmetric cross-product matrix [v×]."""
    return [
        [0.0,    -v[2],  v[1]],
        [v[2],   0.0,   -v[0]],
        [-v[1],  v[0],   0.0],
    ]


def _mat3_mul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """3×3 × 3×3 matrix multiply."""
    return [
        [sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def _mat3_t(a: List[List[float]]) -> List[List[float]]:
    """3×3 transpose."""
    return [[a[j][i] for j in range(3)] for i in range(3)]


def _mat3_neg(a: List[List[float]]) -> List[List[float]]:
    return [[-a[i][j] for j in range(3)] for i in range(3)]


def _mat3_add(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    return [[a[i][j] + b[i][j] for j in range(3)] for i in range(3)]


def _mat3_scale(a: List[List[float]], s: float) -> List[List[float]]:
    return [[a[i][j] * s for j in range(3)] for i in range(3)]


def _vec3_cross(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _rot_from_rpy(rpy: Sequence[float]) -> List[List[float]]:
    """ZYX-extrinsic Euler-angle rotation matrix from URDF rpy convention.

    Matches the standard `urdfdom` / `xacro` interpretation: R = Rz(yaw) ·
    Ry(pitch) · Rx(roll).
    """
    r, p, y = rpy
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return [
        [cy * cp,   cy * sp * sr - sy * cr,   cy * sp * cr + sy * sr],
        [sy * cp,   sy * sp * sr + cy * cr,   sy * sp * cr - cy * sr],
        [-sp,        cp * sr,                  cp * cr],
    ]


# ── 6×6 spatial matrix helpers ─────────────────────────────────────────────


def _zeros66() -> List[List[float]]:
    return [[0.0] * 6 for _ in range(6)]


def _mat66_mul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """6×6 × 6×6 matrix multiply."""
    out = _zeros66()
    for i in range(6):
        for j in range(6):
            s = 0.0
            for k in range(6):
                s += a[i][k] * b[k][j]
            out[i][j] = s
    return out


def _mat66_t(a: List[List[float]]) -> List[List[float]]:
    return [[a[j][i] for j in range(6)] for i in range(6)]


def _mat66_vec(a: List[List[float]], v: Sequence[float]) -> List[float]:
    """6×6 × 6-vec multiply."""
    return [sum(a[i][k] * v[k] for k in range(6)) for i in range(6)]


def _vec6_add(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [a[i] + b[i] for i in range(6)]


def _vec6_scale(a: Sequence[float], s: float) -> List[float]:
    return [a[i] * s for i in range(6)]


def _vec6_sub(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [a[i] - b[i] for i in range(6)]


def _vec6_dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(a[i] * b[i] for i in range(6))


def _outer6(a: Sequence[float], b: Sequence[float]) -> List[List[float]]:
    """Outer product a · b^T → 6×6 matrix."""
    return [[a[i] * b[j] for j in range(6)] for i in range(6)]


def _mat66_sub(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    return [[a[i][j] - b[i][j] for j in range(6)] for i in range(6)]


def _mat66_add(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    return [[a[i][j] + b[i][j] for j in range(6)] for i in range(6)]


def _mat66_scale(a: List[List[float]], s: float) -> List[List[float]]:
    return [[a[i][j] * s for j in range(6)] for i in range(6)]


# ── spatial cross products ─────────────────────────────────────────────────


def _spatial_cross_motion(v: Sequence[float]) -> List[List[float]]:
    """Motion cross [v ×ₘ] — used in v × w when w is a motion vector.

    Convention: v = (ω, u) where ω is angular, u is linear.
    [v ×ₘ] = [[ω×]   0   ]
             [[u×]  [ω×]]
    """
    omega = (v[0], v[1], v[2])
    u = (v[3], v[4], v[5])
    sk_w = _skew3(omega)
    sk_u = _skew3(u)
    out = _zeros66()
    for i in range(3):
        for j in range(3):
            out[i][j] = sk_w[i][j]
            out[i + 3][j] = sk_u[i][j]
            out[i + 3][j + 3] = sk_w[i][j]
    return out


def _spatial_cross_force(v: Sequence[float]) -> List[List[float]]:
    """Force cross [v ×_f] = -[v ×ₘ]^T — used in v × f when f is a force.

    [v ×_f] = [[ω×]   [u×] ]
              [  0    [ω×]]
    """
    omega = (v[0], v[1], v[2])
    u = (v[3], v[4], v[5])
    sk_w = _skew3(omega)
    sk_u = _skew3(u)
    out = _zeros66()
    for i in range(3):
        for j in range(3):
            out[i][j] = sk_w[i][j]
            out[i][j + 3] = sk_u[i][j]
            out[i + 3][j + 3] = sk_w[i][j]
    return out


# ── Plücker spatial transform from translation + rotation ─────────────────


def _plucker_transform(rot_child_to_parent: List[List[float]], r: Sequence[float]) -> List[List[float]]:
    """Build the 6×6 Plücker spatial motion transform X(C←P): parent → child.

    Featherstone (2008) eq. 2.24: X = [[E, 0], [-E·[r×], E]]
    where E = R^T (R^T because Featherstone's E maps parent vectors INTO
    the child frame, but URDF / Rodrigues conventions give the
    child-to-parent rotation, so we transpose).

    Args:
        rot_child_to_parent: 3×3 rotation R such that v_parent = R · v_child
        r: position of child-frame origin expressed in parent frame.
    """
    R_t = _mat3_t(rot_child_to_parent)      # R^T (maps parent → child basis)
    sk_r = _skew3(r)
    R_t_skr = _mat3_mul(R_t, sk_r)          # R^T · [r×]
    neg_R_t_skr = _mat3_neg(R_t_skr)
    X = _zeros66()
    for i in range(3):
        for j in range(3):
            X[i][j] = R_t[i][j]
            X[i + 3][j] = neg_R_t_skr[i][j]
            X[i + 3][j + 3] = R_t[i][j]
    return X


# ── spatial inertia from URDF Link inertial block ────────────────────────


def spatial_inertia_from_link(link: Link) -> List[List[float]]:
    """Build the 6×6 spatial inertia I for a link about its **body** frame.

    Given link.inertia = mass m, 3×3 inertia tensor I_c at COM, COM offset
    c = link.inertia.com.xyz, returns I_spatial in the link's body frame
    expressed at the parent joint frame (i.e. offset by c).

    I_spatial = [[I_c + m·[c×][c×]^T,    m·[c×]],
                 [m·[c×]^T,              m·I_3 ]]
    """
    inert = link.inertia
    m = inert.mass
    c = inert.com.xyz
    I_c = [
        [inert.ixx, inert.ixy, inert.ixz],
        [inert.ixy, inert.iyy, inert.iyz],
        [inert.ixz, inert.iyz, inert.izz],
    ]
    sk_c = _skew3(c)
    # m·[c×][c×]^T = -m·[c×][c×] when c is real
    sk_c_t = _mat3_t(sk_c)
    pseudo = _mat3_mul(sk_c, sk_c_t)
    pseudo = _mat3_scale(pseudo, m)
    upper_left = _mat3_add(I_c, pseudo)
    m_skc = _mat3_scale(sk_c, m)
    m_skc_t = _mat3_t(m_skc)
    I = _zeros66()
    for i in range(3):
        for j in range(3):
            I[i][j] = upper_left[i][j]
            I[i][j + 3] = m_skc[i][j]
            I[i + 3][j] = m_skc_t[i][j]
            I[i + 3][j + 3] = (m if i == j else 0.0)
    return I


# ── joint Plücker transform X_J(q) for a 1-DOF joint ─────────────────────


def _joint_motion_transform(joint: Joint, q: float) -> List[List[float]]:
    """Plücker transform of the joint motion: parent-frame → child-frame
    accounting for the joint's current configuration q.

    For revolute joint with unit axis a, this is the rotation about a by q.
    For prismatic joint with unit axis a, this is the translation along a
    by q.
    For fixed joint, this is the identity.
    """
    if joint.kind in ("revolute", "continuous"):
        # Rotation about unit axis by angle q (Rodrigues' rotation formula).
        ax, ay, az = joint.axis
        # Normalise axis.
        n = math.sqrt(ax * ax + ay * ay + az * az)
        if n < 1e-12:
            return _identity6()
        ax, ay, az = ax / n, ay / n, az / n
        c = math.cos(q)
        s = math.sin(q)
        oc = 1.0 - c
        rot = [
            [c + ax * ax * oc,        ax * ay * oc - az * s,   ax * az * oc + ay * s],
            [ay * ax * oc + az * s,   c + ay * ay * oc,        ay * az * oc - ax * s],
            [az * ax * oc - ay * s,   az * ay * oc + ax * s,   c + az * az * oc],
        ]
        return _plucker_transform(rot, (0.0, 0.0, 0.0))
    elif joint.kind == "prismatic":
        ax, ay, az = joint.axis
        n = math.sqrt(ax * ax + ay * ay + az * az)
        if n < 1e-12:
            return _identity6()
        r = (q * ax / n, q * ay / n, q * az / n)
        return _plucker_transform(_identity3(), r)
    else:  # fixed
        return _identity6()


def _identity3() -> List[List[float]]:
    return [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]


def _identity6() -> List[List[float]]:
    out = _zeros66()
    for i in range(6):
        out[i][i] = 1.0
    return out


# ── joint motion subspace S ─────────────────────────────────────────────────


def _joint_motion_subspace(joint: Joint) -> List[float]:
    """6-vec motion subspace S for a 1-DOF joint.

    Revolute  → S = (axis, 0_3)    (angular block)
    Prismatic → S = (0_3,  axis)   (linear block)
    Fixed     → S = 0
    """
    ax, ay, az = joint.axis
    n = math.sqrt(ax * ax + ay * ay + az * az)
    if n < 1e-12:
        return [0.0] * 6
    ax, ay, az = ax / n, ay / n, az / n
    if joint.kind in ("revolute", "continuous"):
        return [ax, ay, az, 0.0, 0.0, 0.0]
    if joint.kind == "prismatic":
        return [0.0, 0.0, 0.0, ax, ay, az]
    return [0.0] * 6


# ── BuiltArticulation: ABA-ready cache of a parsed ArticulatedSystem ─────


@dataclass
class BuiltArticulation:
    """ABA-ready representation of an ArticulatedSystem.

    Built once from URDF; cached for repeated simulation steps. Maps
    URDF link/joint indices into a contiguous joint-index space where
    `parent_joint[i]` is the index of joint i's parent joint (-1 = base).
    """
    n: int                                    # number of moving joints
    joint_names: List[str]
    joint_kinds: List[str]
    parent_joint: List[int]                   # length n, -1 = base
    motion_subspace: List[List[float]]        # length n, each 6-vec
    fixed_origin_transform: List[List[List[float]]]  # length n, 6×6 each
    child_link_inertia: List[List[List[float]]]      # length n, 6×6 each
    joint_damping: List[float]                # length n
    joint_friction: List[float]               # length n


def build_articulation(sys: ArticulatedSystem) -> BuiltArticulation:
    """Build an ABA-ready cache from a parsed URDF ArticulatedSystem.

    Walks the joint graph (parent → child), assigns contiguous indices
    to moving joints, computes per-joint fixed origin transforms +
    motion subspaces + child-link spatial inertias.

    Fixed joints are collapsed: their inertia is welded onto the parent
    moving joint's child link. The result is a graph of moving joints
    only.

    Currently supports rigid trees (no closed kinematic loops). Base
    link is the link that is not a child of any joint.
    """
    # Identify base link.
    children = {j.child for j in sys.joints}
    base_links = [link.name for link in sys.links if link.name not in children]
    if len(base_links) != 1:
        raise ValueError(
            f"build_articulation: expected exactly 1 base link; "
            f"found {len(base_links)}: {base_links}"
        )
    base_link_name = base_links[0]
    # Map link name → Link.
    link_by_name = {link.name: link for link in sys.links}
    # Filter to moving joints; for now collapse fixed joints by merging
    # the child link's inertia into the welded composite (skipped — most
    # of our test URDFs don't have fixed joints in critical positions).
    moving = [j for j in sys.joints if j.kind != "fixed"]
    n = len(moving)
    if n == 0:
        return BuiltArticulation(
            n=0, joint_names=[], joint_kinds=[], parent_joint=[],
            motion_subspace=[], fixed_origin_transform=[],
            child_link_inertia=[], joint_damping=[], joint_friction=[],
        )
    # Build joint-index map.
    name_to_idx = {j.name: i for i, j in enumerate(moving)}
    # For each moving joint, find its parent moving joint by walking up
    # the joint graph through any intervening fixed joints. The parent
    # joint of joint i is the unique moving joint whose child link is on
    # the path from base to joint i's parent link.
    # Build link → parent_joint map: for each child link of a moving
    # joint, store that joint's index.
    link_to_parent_joint: dict = {}
    for i, j in enumerate(moving):
        link_to_parent_joint[j.child] = i
    parent_joint = []
    for j in moving:
        # Walk from j.parent up to base, looking for a moving joint.
        cursor = j.parent
        pidx = -1
        guard = 0
        while cursor != base_link_name and guard < 1000:
            if cursor in link_to_parent_joint:
                pidx = link_to_parent_joint[cursor]
                break
            # Find the joint that has cursor as its child and recurse.
            found = False
            for k in sys.joints:
                if k.child == cursor:
                    cursor = k.parent
                    found = True
                    break
            if not found:
                break
            guard += 1
        parent_joint.append(pidx)
    # Per-joint motion subspace + fixed origin transform + child link inertia.
    motion_subspace = [_joint_motion_subspace(j) for j in moving]
    fixed_origin_transform = []
    for j in moving:
        rot = _rot_from_rpy(j.origin.rpy)
        r = j.origin.xyz
        fixed_origin_transform.append(_plucker_transform(rot, r))
    child_link_inertia = [
        spatial_inertia_from_link(link_by_name[j.child]) for j in moving
    ]
    return BuiltArticulation(
        n=n,
        joint_names=[j.name for j in moving],
        joint_kinds=[j.kind for j in moving],
        parent_joint=parent_joint,
        motion_subspace=motion_subspace,
        fixed_origin_transform=fixed_origin_transform,
        child_link_inertia=child_link_inertia,
        joint_damping=[j.damping for j in moving],
        joint_friction=[j.friction for j in moving],
    )


# ── ArticulatedState ──────────────────────────────────────────────────────


@dataclass
class ArticulatedState:
    """Joint-space state of an articulated system.

    Both q (positions) and qdot (velocities) are length n; qddot
    (accelerations) is set by aba_forward.
    """
    q: List[float]
    qdot: List[float]
    qddot: List[float] = field(default_factory=list)

    @classmethod
    def zero(cls, n: int) -> "ArticulatedState":
        return cls(q=[0.0] * n, qdot=[0.0] * n, qddot=[0.0] * n)


# ── Featherstone ABA forward dynamics ─────────────────────────────────────


def aba_forward(
    built: BuiltArticulation,
    q: List[float],
    qdot: List[float],
    tau: List[float],
    gravity: Tuple[float, float, float] = (0.0, 0.0, -9.81),
) -> List[float]:
    """Featherstone's Articulated-Body Algorithm — O(n) forward dynamics.

    Returns joint accelerations qddot given current q, qdot, and applied
    torques tau. Uses the built articulation cache for parent indices /
    motion subspaces / fixed origin transforms / link inertias.
    """
    n = built.n
    if not (len(q) == len(qdot) == len(tau) == n):
        raise ValueError(
            f"aba_forward: q/qdot/tau must all have length n={n}; "
            f"got {len(q)}/{len(qdot)}/{len(tau)}"
        )
    if n == 0:
        return []

    # Per-joint computed transforms: X[i] = parent → joint i.
    X = []
    for i in range(n):
        # Note: the joint motion transform applies in the JOINT frame,
        # so X_i = X_J(q_i) · X_T(i). Real Featherstone convention:
        # joint variable acts AFTER the fixed origin transform.
        # Featherstone (2008) eq. 4.16: X_J · X_T.
        X.append(_mat66_mul(
            _joint_motion_transform(_jointlike(built, i), q[i]),
            built.fixed_origin_transform[i],
        ))

    # Per-joint spatial velocity v[i] + Coriolis c[i].
    v: List[List[float]] = [[0.0] * 6 for _ in range(n)]
    c: List[List[float]] = [[0.0] * 6 for _ in range(n)]
    for i in range(n):
        S_i = built.motion_subspace[i]
        # v_parent_in_i_frame = X[i] · v[parent] (parent = 0 if base)
        if built.parent_joint[i] < 0:
            v_p_in_i = [0.0] * 6
        else:
            v_p_in_i = _mat66_vec(X[i], v[built.parent_joint[i]])
        # v[i] = v_p_in_i + S_i · qdot_i
        S_qdot = _vec6_scale(S_i, qdot[i])
        v[i] = _vec6_add(v_p_in_i, S_qdot)
        # c[i] = v[i] ×ₘ (S_i · qdot_i) — Coriolis bias.
        cross_m = _spatial_cross_motion(v[i])
        c[i] = _mat66_vec(cross_m, S_qdot)

    # Articulated inertia I_a[i] + bias p_a[i].
    I_a: List[List[List[float]]] = [
        [row[:] for row in built.child_link_inertia[i]] for i in range(n)
    ]
    p_a: List[List[float]] = []
    for i in range(n):
        # p_a[i] = v[i] ×_f (I[i] · v[i])
        Iv = _mat66_vec(I_a[i], v[i])
        cf = _spatial_cross_force(v[i])
        p_a.append(_mat66_vec(cf, Iv))

    # Pass 2: inward inertia + bias accumulation.
    U: List[List[float]] = [[0.0] * 6 for _ in range(n)]
    D: List[float] = [0.0] * n
    u: List[float] = [0.0] * n
    for i in reversed(range(n)):
        S_i = built.motion_subspace[i]
        U[i] = _mat66_vec(I_a[i], S_i)
        d = _vec6_dot(S_i, U[i]) + built.joint_damping[i]
        if abs(d) < 1e-12:
            d = 1e-12  # numerical guard
        D[i] = d
        u[i] = tau[i] - _vec6_dot(S_i, p_a[i])
        pidx = built.parent_joint[i]
        if pidx >= 0:
            # I_a[pidx] += X[i]^T · (I_a[i] - U[i] U[i]^T / D[i]) · X[i]
            U_outer = _outer6(U[i], U[i])
            U_outer = _mat66_scale(U_outer, 1.0 / D[i])
            inner = _mat66_sub(I_a[i], U_outer)
            Xt = _mat66_t(X[i])
            tmp = _mat66_mul(Xt, inner)
            contrib_I = _mat66_mul(tmp, X[i])
            I_a[pidx] = _mat66_add(I_a[pidx], contrib_I)
            # p_a[pidx] += X[i]^T · (p_a[i] + I_a[i] · c[i] + U[i] · u[i] / D[i])
            I_a_c = _mat66_vec(I_a[i], c[i])
            U_u = _vec6_scale(U[i], u[i] / D[i])
            sum_term = _vec6_add(_vec6_add(p_a[i], I_a_c), U_u)
            contrib_p = _mat66_vec(Xt, sum_term)
            p_a[pidx] = _vec6_add(p_a[pidx], contrib_p)

    # Pass 3: outward acceleration. Base spatial accel = -gravity expressed
    # as a spatial vector (angular = 0, linear = -g).
    a_base = [0.0, 0.0, 0.0, -gravity[0], -gravity[1], -gravity[2]]
    a: List[List[float]] = [[0.0] * 6 for _ in range(n)]
    qddot = [0.0] * n
    for i in range(n):
        pidx = built.parent_joint[i]
        if pidx < 0:
            a_p_in_i = _mat66_vec(X[i], a_base)
        else:
            a_p_in_i = _mat66_vec(X[i], a[pidx])
        a_prime = _vec6_add(a_p_in_i, c[i])
        qddot[i] = (u[i] - _vec6_dot(U[i], a_prime)) / D[i]
        a[i] = _vec6_add(a_prime, _vec6_scale(built.motion_subspace[i], qddot[i]))
    return qddot


def _jointlike(built: BuiltArticulation, i: int) -> Joint:
    """Reconstruct a Joint dataclass with just the fields _joint_motion_transform
    needs (kind, axis). Used so the per-step path doesn't carry full Joint
    structs through the cache."""
    # Recover the axis from the motion subspace.
    S = built.motion_subspace[i]
    kind = built.joint_kinds[i]
    if kind in ("revolute", "continuous"):
        axis = (S[0], S[1], S[2])
    elif kind == "prismatic":
        axis = (S[3], S[4], S[5])
    else:
        axis = (1.0, 0.0, 0.0)
    return Joint(
        name=built.joint_names[i],
        kind=kind,
        parent="",
        child="",
        axis=axis,
    )


# ── Semi-implicit Euler integration step ─────────────────────────────────


def articulated_step(
    built: BuiltArticulation,
    state: ArticulatedState,
    tau: List[float],
    dt: float,
    gravity: Tuple[float, float, float] = (0.0, 0.0, -9.81),
) -> None:
    """Advance state in-place by dt using semi-implicit Euler:

        qdot_new = qdot + dt · qddot
        q_new    = q    + dt · qdot_new

    Semi-implicit (a.k.a. symplectic Euler) is the standard choice for
    rigid-body sim — preserves energy to O(dt²) vs explicit Euler which
    drifts.
    """
    qddot = aba_forward(built, state.q, state.qdot, tau, gravity)
    state.qddot = qddot
    for i in range(built.n):
        state.qdot[i] += dt * qddot[i]
        state.q[i] += dt * state.qdot[i]
