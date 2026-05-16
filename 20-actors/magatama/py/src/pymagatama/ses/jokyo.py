"""SES jokyo DB helpers — Phase 2 (ADR-2605120000).

Wraps the forbidden-transition check from state.py with a DB lookup
of the current jokyo for an existing anken.
"""

from __future__ import annotations

from typing import Optional

from pymagatama.db_sync import sync_cursor
from pymagatama.ses.state import is_forbidden_transition


def fetch_current_jokyo(anken_vertex_id: str) -> Optional[str]:
    """Return the latest jokyo value for the given anken, or None."""
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT jokyo FROM mv_ses_anken_latest_jokyo
            WHERE anken_vertex_id = %s
            LIMIT 1
            """,
            (anken_vertex_id,),
        )
        row = cur.fetchone()
    return row[0] if row else None


def validate_transition(
    anken_vertex_id: Optional[str],
    next_jokyo: str,
) -> tuple[bool, Optional[str]]:
    """Check whether transitioning to *next_jokyo* is allowed.

    Returns:
        (allowed, current_jokyo)
        allowed=True means the INSERT should proceed.
    """
    if not anken_vertex_id:
        return True, None

    current = fetch_current_jokyo(anken_vertex_id)
    if is_forbidden_transition(current, next_jokyo):
        return False, current
    return True, current
