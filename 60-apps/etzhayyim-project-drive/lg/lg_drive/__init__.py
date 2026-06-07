"""lg-drive — drive.etzhayyim.com compat API backend.

Canonical XRPC methods (ai.etzhayyim.apps.drive.*) backed by kotoba datomic
(graph ``drive-v1``), exposed as a Google Drive v3 + Microsoft Graph (OneDrive)
compatible REST API by the ``drive-compat`` Cloudflare Worker edge.

See 90-docs/adr/2606010500-workspace-compat-datomic-schema.md.
"""

__version__ = "0.1.0"
