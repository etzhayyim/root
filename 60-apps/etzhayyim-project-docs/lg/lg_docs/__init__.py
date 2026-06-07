"""lg-docs — docs.etzhayyim.com compat API backend.

Canonical XRPC methods (ai.etzhayyim.apps.docs.*) backed by kotoba datomic
(graph ``docs-v1``), exposed as a Google Docs v1 + Microsoft Graph (Word)
compatible REST API by the ``docs-compat`` Cloudflare Worker edge.

See 90-docs/adr/2606010500-workspace-compat-datomic-schema.md.
"""

__version__ = "0.1.0"
