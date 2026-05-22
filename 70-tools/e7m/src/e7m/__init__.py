"""e7m — etzhayyim operator surface.

This package is the **only sanctioned external interface** for the
religious-corp artificial-organism ecosystem. Per ADR-2605192100 §1.3
(decision attribution = etzhayyim) and §1.6 (substrate boundary), other
agents (Claude in other sessions, automation, sister-corp organisms) must
touch etzhayyim through `e7m` CLI or the e7m MCP server — never via
direct `kubectl`, raw file edits, or ad-hoc `curl`.

Why: every meaningful interaction is then logged + auditable + auth-able
at one chokepoint, and the substrate boundary lints can enforce that
chokepoint without scanning the entire universe of possible client code.
"""

__version__ = "0.1.0"
