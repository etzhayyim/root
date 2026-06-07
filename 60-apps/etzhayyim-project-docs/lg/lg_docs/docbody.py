"""Structural document body + batchUpdate edit engine.

The body is an ordered list of structural elements:
  ``{elementId, kind, headingLevel?, text}``  (kind ∈ paragraph|heading|listItem|…)

A global character index addresses the document the way Google Docs does: each
element contributes ``len(text)`` index positions followed by one newline
separator. ``index_to_pos`` maps a global index to ``(element_idx, local_offset)``.

The supported ``batchUpdate`` request ops are a canonical superset of the Google
Docs Request set; ``apply_request`` mutates the body in place. Cross-element
``deleteRange`` merges the partial start/end elements (start element's kind wins).
"""

from __future__ import annotations

from typing import Any

from . import ids


def doc_length(body: list[dict[str, Any]]) -> int:
    """Total global index length (text + 1 newline per element)."""
    return sum(len(e.get("text", "")) + 1 for e in body)


def flatten_text(body: list[dict[str, Any]]) -> str:
    return "\n".join(e.get("text", "") for e in body)


def with_indices(body: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a copy of body with computed startIndex/endIndex per element."""
    out: list[dict[str, Any]] = []
    pos = 0
    for e in body:
        text = e.get("text", "")
        item = {"elementId": e.get("elementId"), "kind": e.get("kind", "paragraph"), "text": text,
                "startIndex": pos, "endIndex": pos + len(text)}
        if e.get("headingLevel") is not None:
            item["headingLevel"] = e["headingLevel"]
        out.append(item)
        pos += len(text) + 1
    return out


def index_to_pos(body: list[dict[str, Any]], index: int) -> tuple[int, int]:
    """Map a global index to (element_idx, local_offset). Clamps to the doc end."""
    pos = 0
    for i, e in enumerate(body):
        tlen = len(e.get("text", ""))
        if index <= pos + tlen:
            return i, max(0, index - pos)
        pos += tlen + 1
    # past the end → end of last element
    if body:
        return len(body) - 1, len(body[-1].get("text", ""))
    return 0, 0


def _new_paragraph(text: str, kind: str = "paragraph", heading_level: int | None = None) -> dict[str, Any]:
    e: dict[str, Any] = {"elementId": ids.new_element_id(), "kind": kind, "text": text}
    if heading_level is not None:
        e["headingLevel"] = heading_level
    return e


def apply_request(body: list[dict[str, Any]], req: dict[str, Any]) -> None:
    op = req.get("op")
    if op == "appendParagraph":
        body.append(_new_paragraph(req.get("text", "")))
    elif op == "insertHeading":
        body.append(_new_paragraph(req.get("text", ""), kind="heading", heading_level=req.get("headingLevel", 1)))
    elif op == "replaceText":
        match, repl = req.get("matchText", ""), req.get("text", "")
        if match:
            for e in body:
                if match in e.get("text", ""):
                    e["text"] = e["text"].replace(match, repl)
    elif op == "insertText":
        if not body:
            body.append(_new_paragraph(""))
        i, off = index_to_pos(body, int(req.get("index", 0)))
        t = body[i].get("text", "")
        body[i]["text"] = t[:off] + req.get("text", "") + t[off:]
    elif op == "deleteRange":
        _delete_range(body, int(req.get("startIndex", 0)), int(req.get("endIndex", 0)))


def _delete_range(body: list[dict[str, Any]], start: int, end: int) -> None:
    if not body or end <= start:
        return
    si, so = index_to_pos(body, start)
    ei, eo = index_to_pos(body, end)
    if si == ei:
        t = body[si].get("text", "")
        body[si]["text"] = t[:so] + t[eo:]
        return
    # span: keep head of start elem + tail of end elem, drop the middle, merge.
    head = body[si].get("text", "")[:so]
    tail = body[ei].get("text", "")[eo:]
    body[si]["text"] = head + tail
    del body[si + 1:ei + 1]
