"""keiei (経営) — C-suite AI role layer.

ADR 2605101200. Operating entity = amanomibashira. Vendor = Gftd Japan.
"""

from .roles import ROLES, CxoRole, GateVerdict, by_id, gate

__all__ = ["ROLES", "CxoRole", "GateVerdict", "by_id", "gate"]
