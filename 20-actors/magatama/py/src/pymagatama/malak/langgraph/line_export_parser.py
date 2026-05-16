"""Parse Android LINE chat-history text export → scam_intake events.

Android LINE app export format (UTF-8 text):

    [LINE] <room name>のトーク履歴
    保存日時：YYYY/MM/DD HH:MM

    YYYY/MM/DD(曜)
    HH:MM\tSenderName\tMessage body line 1
                     \tcontinuation
    HH:MM\tSenderName\tAnother message

Lines starting with date header reset the current date.
Lines starting with HH:MM\tname\tbody are message lines.
Bare continuation lines (no time prefix) are appended to the previous message.

Usage:
    msgs = parse_line_export(Path("~/Downloads/line-talk.txt"))
    for m in msgs: await run_scam_intake("line", to_intake_envelope(m, room))
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


HEADER_RE = re.compile(r"^\[LINE\]\s*(?P<room>.+?)\s*(?:のトーク履歴|/.*)?$")
DATE_RE = re.compile(r"^(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})(?:\([^)]+\))?\s*$")
MSG_RE = re.compile(r"^(?P<hh>\d{2}):(?P<mm>\d{2})\t(?P<sender>[^\t]+)\t(?P<body>.*)$")


@dataclass
class LineMessage:
    room: str
    timestamp_iso: str  # YYYY-MM-DDTHH:MM:00+09:00
    sender: str
    body: str


def parse_line_export(path: Path) -> list[LineMessage]:
    """Read an Android LINE text export and return ordered messages."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return list(_parse_lines(text.splitlines()))


def _parse_lines(lines: list[str]) -> Iterator[LineMessage]:
    room = ""
    cur_date = ""  # YYYY-MM-DD
    cur_msg: LineMessage | None = None

    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line.strip():
            continue

        if not room:
            m = HEADER_RE.match(line)
            if m:
                room = m.group("room").strip()
                continue

        m = DATE_RE.match(line)
        if m:
            if cur_msg:
                yield cur_msg
                cur_msg = None
            cur_date = f"{m['y']}-{m['m']}-{m['d']}"
            continue

        m = MSG_RE.match(line)
        if m:
            if cur_msg:
                yield cur_msg
            ts = f"{cur_date}T{m['hh']}:{m['mm']}:00+09:00" if cur_date else f"{m['hh']}:{m['mm']}"
            cur_msg = LineMessage(
                room=room or "unknown",
                timestamp_iso=ts,
                sender=m["sender"].strip(),
                body=m["body"],
            )
            continue

        if cur_msg is not None:
            cur_msg.body = (cur_msg.body + "\n" + line).strip()

    if cur_msg:
        yield cur_msg


def to_intake_envelope(msg: LineMessage, *, tlp: str = "AMBER") -> dict:
    """Convert a LineMessage into the dict shape expected by run_scam_intake('line', ...)."""
    return {
        "destination": f"line:room:{msg.room}",
        "source": {"userId": msg.sender, "roomName": msg.room},
        "message": {"id": f"{msg.timestamp_iso}|{msg.sender}", "type": "text", "text": msg.body},
        "timestamp": msg.timestamp_iso,
        "tlp": tlp,
    }
