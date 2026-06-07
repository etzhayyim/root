"""lg-sheets — sheets.etzhayyim.com compat API backend.

Canonical XRPC methods (ai.etzhayyim.apps.sheets.*) backed by kotoba datomic
(graph ``sheets-v1``), exposed as a Google Sheets v4 + Microsoft Graph
(workbook) compatible REST API by the ``sheets-compat`` Cloudflare Worker edge.

See 90-docs/adr/2606010500-workspace-compat-datomic-schema.md.
"""

__version__ = "0.1.0"
