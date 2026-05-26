"""isaaclab.utils — small utility surfaces shared across isaaclab.*.

R1.x scope:
  - dr   — domain randomisation primitives (sim2real config)
  - math — quaternion + Euler + axis-angle + slerp + frame transform helpers
  - dict — cfg serialization (class_to_dict / update_class_from_dict /
           deep_update / print_dict / dict_to_md_table / slice round-trip)
"""

from . import dict, dr, math

__all__ = ["dict", "dr", "math"]
