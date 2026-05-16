from __future__ import annotations

import os
import re
from collections.abc import Iterable
from typing import Any

from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine


_VARCHAR_LENGTH_RE = re.compile(
    r"\b(?:VARCHAR|CHARACTER\s+VARYING)\s*\(\s*\d+\s*\)",
    re.IGNORECASE,
)


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is required (postgres://user:pass@host:port/db)")
    return url


def make_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url(), pool_pre_ping=True)


def split_sql(sql_text: str) -> list[str]:
    statements: list[str] = []
    chars: list[str] = []
    quote: str | None = None
    dollar_tag: str | None = None
    i = 0
    while i < len(sql_text):
        ch = sql_text[i]
        nxt = sql_text[i + 1] if i + 1 < len(sql_text) else ""

        if dollar_tag:
            chars.append(ch)
            if sql_text.startswith(dollar_tag, i):
                chars.extend(sql_text[i + 1 : i + len(dollar_tag)])
                i += len(dollar_tag)
                dollar_tag = None
                continue
            i += 1
            continue

        if quote:
            chars.append(ch)
            if ch == quote:
                if nxt == quote:
                    chars.append(nxt)
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if ch == "-" and nxt == "-":
            i += 2
            while i < len(sql_text) and sql_text[i] not in "\r\n":
                i += 1
            if i < len(sql_text):
                chars.append(sql_text[i])
                i += 1
            continue

        if ch in {"'", '"'}:
            quote = ch
            chars.append(ch)
            i += 1
            continue

        if ch == "$":
            end = sql_text.find("$", i + 1)
            if end != -1:
                tag = sql_text[i : end + 1]
                if tag == "$$" or tag[1:-1].replace("_", "").isalnum():
                    dollar_tag = tag
                    chars.append(tag)
                    i = end + 1
                    continue

        if ch == ";":
            statement = "".join(chars).strip()
            if statement:
                statements.append(statement)
            chars = []
            i += 1
            continue

        chars.append(ch)
        i += 1

    tail = "".join(chars).strip()
    if tail:
        statements.append(tail)
    return statements


def _rewrite_risingwave_statement(statement: str) -> str:
    chars: list[str] = []
    quote: str | None = None
    dollar_tag: str | None = None
    i = 0
    while i < len(statement):
        ch = statement[i]
        nxt = statement[i + 1] if i + 1 < len(statement) else ""

        if dollar_tag:
            chars.append(ch)
            if statement.startswith(dollar_tag, i):
                chars.extend(statement[i + 1 : i + len(dollar_tag)])
                i += len(dollar_tag)
                dollar_tag = None
                continue
            i += 1
            continue

        if quote:
            chars.append(ch)
            if ch == quote:
                if nxt == quote:
                    chars.append(nxt)
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if ch in {"'", '"'}:
            quote = ch
            chars.append(ch)
            i += 1
            continue

        if ch == "$":
            end = statement.find("$", i + 1)
            if end != -1:
                tag = statement[i : end + 1]
                if tag == "$$" or tag[1:-1].replace("_", "").isalnum():
                    dollar_tag = tag
                    chars.append(tag)
                    i = end + 1
                    continue

        match = _VARCHAR_LENGTH_RE.match(statement, i)
        if match:
            chars.append("VARCHAR")
            i = match.end()
            continue

        chars.append(ch)
        i += 1
    return "".join(chars)


def execute_statements(conn: Connection, statements: Iterable[str], *, flush: bool = False) -> None:
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    for statement in statements:
        rewritten = _rewrite_risingwave_statement(statement).strip()
        if not rewritten or all(
            not line.strip() or line.strip().startswith("--")
            for line in rewritten.splitlines()
        ):
            continue
        conn.exec_driver_sql(rewritten)
    if flush:
        conn.exec_driver_sql("FLUSH")


def execute_sql_text(conn: Connection, sql_text: str, *, flush: bool = False) -> None:
    execute_statements(conn, split_sql(sql_text), flush=flush)


def _named_bind_sql(sql: str) -> str:
    chars: list[str] = []
    quote: str | None = None
    dollar_tag: str | None = None
    i = 0
    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""

        if dollar_tag:
            chars.append(ch)
            if sql.startswith(dollar_tag, i):
                chars.extend(sql[i + 1 : i + len(dollar_tag)])
                i += len(dollar_tag)
                dollar_tag = None
                continue
            i += 1
            continue

        if quote:
            chars.append(ch)
            if ch == quote:
                if nxt == quote:
                    chars.append(nxt)
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if ch in {"'", '"'}:
            quote = ch
            chars.append(ch)
            i += 1
            continue

        if ch == "$":
            if nxt.isdigit():
                j = i + 1
                while j < len(sql) and sql[j].isdigit():
                    j += 1
                chars.append(f":p{int(sql[i + 1:j]) - 1}")
                i = j
                continue
            end = sql.find("$", i + 1)
            if end != -1:
                tag = sql[i : end + 1]
                if tag == "$$" or tag[1:-1].replace("_", "").isalnum():
                    dollar_tag = tag
                    chars.append(tag)
                    i = end + 1
                    continue

        chars.append(ch)
        i += 1
    return "".join(chars)


def execute_bound_statements(
    conn: Connection,
    statements: Iterable[dict[str, Any]],
    *,
    flush: bool = False,
) -> None:
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    for statement in statements:
        sql = str(statement["sql"])
        parameters = list(statement.get("parameters") or [])
        if parameters:
            params = {f"p{i}": value for i, value in enumerate(parameters)}
            conn.execute(text(_named_bind_sql(_rewrite_risingwave_statement(sql))), params)
        else:
            conn.exec_driver_sql(_rewrite_risingwave_statement(sql))
    if flush:
        conn.exec_driver_sql("FLUSH")
