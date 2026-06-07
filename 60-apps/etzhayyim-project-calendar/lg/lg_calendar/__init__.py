"""lg-calendar — calendar.etzhayyim.com compat API backend.

Canonical XRPC methods (ai.etzhayyim.apps.calendar.*) backed by kotoba datomic
(graph ``calendar-v1``), exposed as a Google Calendar v3 + Microsoft Graph
compatible REST API by the ``calendar-compat`` Cloudflare Worker edge.

See 90-docs/adr/2606010500-workspace-compat-datomic-schema.md.
"""

__version__ = "0.1.0"
