"""Backward-compat shim — workflows have moved to `generators.<backend>`.

Existing call sites (`from .workflow import hunyuan3d_workflow`) keep
working; new code should `from .generators import GENERATOR_REGISTRY,
hunyuan3d_workflow, pixal3d_request_body`.
"""

from .generators.hunyuan3d import hunyuan3d_workflow  # noqa: F401
from .generators.pixal3d import pixal3d_request_body  # noqa: F401
