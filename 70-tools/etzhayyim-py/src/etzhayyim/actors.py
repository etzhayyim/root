"""actors — Actor lifecycle commands (Python port of actors_shinka.go).

actors shinka: parallel LLM calls to Ollama or Murakumo to generate domain
knowledge, then writes results to PDS via com.atproto.repo.applyWrites.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import click
import httpx

from .auth import auth_headers, resolve_pds

_DEFAULT_OLLAMA = "http://127.0.0.1:11434"
_DEFAULT_MODEL = "gemma3:4b"
_MURAKUMO_URL = "https://murakumo.etzhayyim.com"


# ── data types ────────────────────────────────────────────────────────────────

@dataclass
class ActorInfo:
    did: str
    nanoid: str
    handle: str = ""
    display_name: str = ""
    description: str = ""
    project_id: str = ""


@dataclass
class SubDID:
    path: str
    display_name: str
    description: str


@dataclass
class KEdge:
    from_: str
    relation: str
    to: str


@dataclass
class ShinkaResult:
    did: str
    nanoid: str
    domain_summary: str = ""
    sub_dids: list[SubDID] = field(default_factory=list)
    knowledge_edges: list[KEdge] = field(default_factory=list)
    error: str = ""


# ── LLM backends ─────────────────────────────────────────────────────────────

async def _check_ollama(client: httpx.AsyncClient, base: str, model: str) -> None:
    resp = await client.get(f"{base}/api/tags", timeout=10)
    resp.raise_for_status()
    tags = resp.json()
    names = [m["name"] for m in tags.get("models", [])]
    if not any(n.startswith(model) or model.startswith(n.split(":")[0]) for n in names):
        raise click.ClickException(
            f"Model {model!r} not found in ollama (available: {len(names)} models). "
            f"Run: ollama pull {model}"
        )


async def _ollama_generate(client: httpx.AsyncClient, base: str, model: str, prompt: str) -> str:
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.3, "num_predict": 2048},
    }
    resp = await client.post(f"{base}/api/generate", json=body, timeout=120)
    if resp.status_code != 200:
        raise click.ClickException(f"ollama {resp.status_code}: {resp.text[:200]}")
    return resp.json()["response"]


async def _check_murakumo(client: httpx.AsyncClient, base: str, api_key: str) -> None:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    resp = await client.get(f"{base}/api/openai/v1/models", headers=headers, timeout=10)
    if resp.status_code != 200:
        raise click.ClickException(f"murakumo {resp.status_code}: {resp.text[:200]}")


async def _murakumo_generate(client: httpx.AsyncClient, base: str, api_key: str, model: str, prompt: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a domain knowledge architect. Always respond with valid JSON only. No markdown fences, no explanations, no preamble — just the JSON object."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }
    resp = await client.post(f"{base}/api/openai/v1/chat/completions", json=body, headers=headers, timeout=200)
    if resp.status_code != 200:
        raise click.ClickException(f"murakumo {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ── actor processing ──────────────────────────────────────────────────────────

_RE_JSON_BLOCK = re.compile(r'\{[\s\S]+\}', re.DOTALL)


def _build_prompt(actor: ActorInfo) -> str:
    parts = [f'nanoid={actor.nanoid!r}', f'handle={actor.handle!r}']
    if actor.display_name:
        parts.append(f'displayName={actor.display_name!r}')
    if actor.description:
        parts.append(f'description={actor.description!r}')
    ctx = ", ".join(parts)

    return f"""You are a domain knowledge architect for an AI agent platform called etzhayyim.com.
Given an AI agent's identity metadata, generate structured domain knowledge as JSON.

Actor metadata: {ctx}

Output a JSON object with exactly these keys:
- "domain_summary": 2-3 sentences describing this agent's domain, purpose, and key capabilities
- "sub_dids": array of 3-5 sub-entities this agent manages, each with "path" (URL-safe slug), "display_name", "description"
- "knowledge_edges": array of 5-8 edges, each with "from": "{actor.nanoid}", "relation", "to" (specific concept)

Relations available: EXPERTISE_IN, DEPENDS_ON, PRODUCES, CONSUMES, REGULATES, SERVES, MONITORS, ANALYZES

Output ONLY valid JSON:"""


def _parse_result(actor: ActorInfo, llm_text: str) -> ShinkaResult:
    m = _RE_JSON_BLOCK.search(llm_text)
    if not m:
        return ShinkaResult(did=actor.did, nanoid=actor.nanoid, error="no JSON in LLM response")
    try:
        parsed = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        return ShinkaResult(did=actor.did, nanoid=actor.nanoid, error=f"JSON parse: {exc}")

    sub_dids = [
        SubDID(path=_sanitize_path(s.get("path", "")),
               display_name=s.get("display_name", ""),
               description=s.get("description", ""))
        for s in parsed.get("sub_dids", [])
        if s.get("path")
    ]
    edges = [
        KEdge(from_=e.get("from", actor.nanoid),
              relation=e.get("relation", ""),
              to=e.get("to", ""))
        for e in parsed.get("knowledge_edges", [])
        if e.get("relation") and e.get("to")
    ]
    return ShinkaResult(
        did=actor.did, nanoid=actor.nanoid,
        domain_summary=parsed.get("domain_summary", ""),
        sub_dids=sub_dids, knowledge_edges=edges,
    )


def _sanitize_path(path: str) -> str:
    path = path.lower().replace(" ", "-")
    return "".join(c for c in path if c.isalnum() or c == "-")


def _stable_rkey(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:16]


# ── PDS fetch / write ─────────────────────────────────────────────────────────

async def _fetch_actors(client: httpx.AsyncClient, pds_url: str, limit: int) -> list[ActorInfo]:
    actors: list[ActorInfo] = []
    cursor = ""
    page = 50
    headers = auth_headers()

    while len(actors) < limit:
        payload: dict[str, Any] = {"status": "active", "batchLimit": page}
        if cursor:
            payload["cursor"] = cursor
        resp = await client.post(f"{pds_url}/xrpc/com.etzhayyim.actor.list", json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            click.echo(f"[shinka] com.etzhayyim.actor.list → {resp.status_code}: {resp.text[:200]}", err=True)
            break
        data = resp.json()
        batch = data.get("actors", [])
        if not batch:
            break
        for a in batch:
            actors.append(ActorInfo(
                did=a.get("did", ""),
                nanoid=a.get("nanoid", ""),
                handle=a.get("handle", ""),
                display_name=a.get("displayName", ""),
                description=a.get("description", ""),
                project_id=a.get("projectId", ""),
            ))
        cursor = data.get("cursor", "")
        if not cursor or len(batch) < page:
            break

    return actors[:limit]


async def _write_result(client: httpx.AsyncClient, pds_url: str, actor: ActorInfo, result: ShinkaResult) -> None:
    now = datetime.now(timezone.utc).isoformat()
    writes: list[dict] = []

    if result.domain_summary:
        writes.append({
            "action": "update", "collection": "com.etzhayyim.actor.app", "rkey": actor.nanoid,
            "value": {"nanoid": actor.nanoid, "did": actor.did,
                      "displayName": actor.display_name, "description": result.domain_summary},
        })

    for sub in result.sub_dids:
        if not sub.path:
            continue
        writes.append({
            "action": "update", "collection": "com.etzhayyim.identity.did",
            "rkey": _stable_rkey(f"did:{sub.path}"),
            "value": {
                "id": f"{actor.did}:{sub.path}", "display_name": sub.display_name,
                "description": sub.description, "status": "active", "controller": actor.did,
                "actorDid": actor.did, "sourceType": "shinka",
                "sourceId": f"shinka:{actor.nanoid}", "created_at": now,
            },
        })

    for edge in result.knowledge_edges:
        key = f"{edge.from_}:{edge.relation}:{edge.to}"
        writes.append({
            "action": "update", "collection": "com.etzhayyim.actor.knowledgeEdge",
            "rkey": _stable_rkey(key),
            "value": {"from": edge.from_, "relation": edge.relation, "to": edge.to, "createdAt": now},
        })

    headers = auth_headers()
    for i in range(0, len(writes), 50):
        batch = writes[i:i + 50]
        resp = await client.post(
            f"{pds_url}/xrpc/com.atproto.repo.applyWrites",
            json={"repo": actor.did, "writes": batch},
            headers=headers, timeout=30,
        )
        if resp.status_code >= 400:
            click.echo(f"[shinka] applyWrites → {resp.status_code}: {resp.text[:200]}", err=True)


# ── main shinka loop ──────────────────────────────────────────────────────────

async def _run_shinka(
    pds_url: str, model: str, limit: int, actor_filter: str,
    dry_run: bool, json_out: bool, concurrency: int,
    use_murakumo: bool, ollama_base: str, murakumo_url: str,
) -> None:
    async with httpx.AsyncClient() as client:
        # Validate LLM backend
        api_key = os.environ.get("MURAKUMO_API_KEY", "")
        if use_murakumo:
            await _check_murakumo(client, murakumo_url, api_key)
            click.echo(f"Using Murakumo ({murakumo_url}) model={model}", err=True)

            async def generate(prompt: str) -> str:
                return await _murakumo_generate(client, murakumo_url, api_key, model, prompt)
        else:
            await _check_ollama(client, ollama_base, model)

            async def generate(prompt: str) -> str:
                return await _ollama_generate(client, ollama_base, model, prompt)

        # Fetch actors
        actors = await _fetch_actors(client, pds_url, limit)
        if actor_filter:
            f = actor_filter.lower()
            actors = [a for a in actors
                      if f in a.nanoid.lower() or f in a.project_id.lower()
                      or f in a.handle.lower() or f in a.did.lower()]

        click.echo(f"Processing {len(actors)} actors with {model} (concurrency={concurrency})", err=True)

        results: list[ShinkaResult] = [ShinkaResult(did="", nanoid="")] * len(actors)
        sem = asyncio.Semaphore(concurrency)
        processed = 0

        async def process_one(idx: int, actor: ActorInfo) -> None:
            nonlocal processed
            async with sem:
                prompt = _build_prompt(actor)
                try:
                    llm_text = await generate(prompt)
                    result = _parse_result(actor, llm_text)
                except Exception as exc:
                    result = ShinkaResult(did=actor.did, nanoid=actor.nanoid, error=str(exc))

                results[idx] = result

                if not dry_run and not result.error:
                    await _write_result(client, pds_url, actor, result)

                processed += 1
                if not json_out:
                    click.echo(f"\r[{processed}/{len(actors)}] {actor.nanoid}", nl=False, err=True)

        await asyncio.gather(*[process_one(i, a) for i, a in enumerate(actors)])

        if not json_out:
            click.echo("", err=True)

        if json_out:
            out = [
                {"did": r.did, "nanoid": r.nanoid, "domain_summary": r.domain_summary,
                 "sub_dids": [{"path": s.path, "display_name": s.display_name, "description": s.description}
                               for s in r.sub_dids],
                 "knowledge_edges": [{"from": e.from_, "relation": e.relation, "to": e.to}
                                      for e in r.knowledge_edges],
                 "error": r.error}
                for r in results
            ]
            click.echo(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            ok = sum(1 for r in results if not r.error)
            click.echo(f"actors shinka: {ok}/{len(results)} processed" +
                       (" (dry-run)" if dry_run else ""))


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.group("actors")
def actors() -> None:
    """Actor lifecycle management."""


@actors.command("shinka")
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--model", default=os.environ.get("etzhayyim_SHINKA_MODEL", _DEFAULT_MODEL), show_default=True,
              help="LLM model name")
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--filter", "actor_filter", default="", help="nanoid/projectId/handle filter")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--concurrency", default=4, type=int, show_default=True)
@click.option("--murakumo/--no-murakumo", default=True,
              help="Use Murakumo OpenAI-compatible API (default). --no-murakumo uses Ollama.")
@click.option("--murakumo-url", default=os.environ.get("etzhayyim_MURAKUMO", _MURAKUMO_URL), show_default=True)
@click.option("--ollama", "ollama_base", default=os.environ.get("OLLAMA_BASE", _DEFAULT_OLLAMA), show_default=True)
def actors_shinka(pds: str | None, model: str, limit: int, actor_filter: str,
                  dry_run: bool, json_out: bool, concurrency: int,
                  murakumo: bool, murakumo_url: str, ollama_base: str) -> None:
    """Generate domain knowledge for actors via LLM (parallel httpx calls to Murakumo or Ollama).

    Fetches actors from PDS, calls LLM for each, writes results via
    com.atproto.repo.applyWrites (domain_summary, sub_dids, knowledge_edges).
    """
    pds_url = (pds or resolve_pds()).rstrip("/")
    asyncio.run(_run_shinka(
        pds_url=pds_url, model=model, limit=limit, actor_filter=actor_filter,
        dry_run=dry_run, json_out=json_out, concurrency=concurrency,
        use_murakumo=murakumo, ollama_base=ollama_base, murakumo_url=murakumo_url,
    ))


@actors.command("jokyo")
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--filter", "actor_filter", default="", help="Substring filter on app name/nanoid")
@click.option("--nanoid", "single_nanoid", default="", help="Single app nanoid to inspect")
@click.option("--limit", default=0, type=int, help="Limit output (0 = all)")
@click.option("--live", is_flag=True, default=True, help="POST /_heartbeat to test ReAct loop")
@click.option("--no-live", "live", flag_value=False)
@click.option("--concurrency", default=16, type=int, show_default=True)
@click.option("--timeout", default=15, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
def actors_jokyo(pds: str | None, actor_filter: str, single_nanoid: str, limit: int,
                 live: bool, concurrency: int, timeout: int, json_out: bool,
                 workspace_dir: str | None) -> None:
    """Autonomous agent health scoring (HTTP health + heartbeat per actor)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from .shannon import _resolve_root
    import time

    pds_url = (pds or resolve_pds()).rstrip("/")
    ws = _resolve_root(workspace_dir)

    # Discover actors from workspace kotodama.jsonld files
    discovered = []
    for p in ws.rglob("kotodama.jsonld"):
        try:
            data = json.loads(p.read_text(errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        nanoid = data.get("nanoid", "")
        name = data.get("name", "")
        if not nanoid:
            continue
        if single_nanoid and nanoid != single_nanoid:
            continue
        if actor_filter and actor_filter not in nanoid and actor_filter not in name:
            continue
        discovered.append({"nanoid": nanoid, "name": name,
                           "did": data.get("@id", f"did:web:{nanoid}.etzhayyim.com")})

    if not discovered:
        click.echo("No actors found", err=True)
        return

    click.echo(f"==> Analyzing jokyo for {len(discovered)} actors (live={live})...\n",
               err=True)

    def analyze(app: dict) -> dict:
        nanoid = app["nanoid"]
        base = f"https://{nanoid}.etzhayyim.com"
        result: dict = {"nanoid": nanoid, "name": app["name"], "did": app["did"],
                        "health_ok": False, "heartbeat_ok": False,
                        "health_ms": 0, "heartbeat_ms": 0, "total_score": 0}
        client = httpx.Client(timeout=timeout)
        try:
            t0 = time.monotonic()
            r = client.get(f"{base}/health")
            result["health_ms"] = int((time.monotonic() - t0) * 1000)
            result["health_ok"] = r.status_code == 200
        except Exception:
            pass

        if live:
            try:
                headers = {}
                try:
                    headers = auth_headers()
                except Exception:
                    pass
                t0 = time.monotonic()
                r = client.post(f"{base}/_heartbeat",
                                json={"feed": "[]", "engagement": "{}"},
                                headers=headers)
                result["heartbeat_ms"] = int((time.monotonic() - t0) * 1000)
                result["heartbeat_ok"] = r.status_code in (200, 201)
            except Exception:
                pass
        client.close()

        score = 0
        if result["health_ok"]:
            score += 40
        if result["heartbeat_ok"]:
            score += 40
        if result["health_ms"] < 200:
            score += 10
        if result["heartbeat_ms"] < 500:
            score += 10
        result["total_score"] = score
        result["grade"] = ("S" if score >= 90 else "A" if score >= 70 else
                           "B" if score >= 50 else "C" if score >= 30 else "D")
        return result

    results = []
    sem_count = min(concurrency, len(discovered))
    with ThreadPoolExecutor(max_workers=sem_count) as pool:
        futures = {pool.submit(analyze, app): app for app in discovered}
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: -r["total_score"])
    if limit > 0:
        results = results[:limit]

    if json_out:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  {'nanoid':<20} {'name':<25} {'health':<8} {'hb':<8} {'score':<6} grade")
        click.echo("  " + "-" * 75)
        for r in results:
            health = f"{'✓' if r['health_ok'] else '✗'} {r['health_ms']}ms"
            hb = f"{'✓' if r['heartbeat_ok'] else '✗'} {r['heartbeat_ms']}ms"
            click.echo(f"  {r['nanoid']:<20} {r['name']:<25} {health:<8} {hb:<8} "
                       f"{r['total_score']:<6} {r['grade']}")


@actors.command("migrate-to-plc")
@click.option("--actor", required=True, help="actor name in deps.toml")
@click.option("--handle", default="", help="handle (default: {actor}.etzhayyim.com)")
@click.option("--apply", is_flag=True, default=False, help="write DID back to deps.toml")
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--offline", is_flag=True, default=False, help="mock PDS response")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--deps", "deps_path", default="deps.toml")
def actors_migrate_to_plc(
    actor: str, handle: str, apply: bool, pds: str | None,
    offline: bool, json_out: bool, deps_path: str,
) -> None:
    """Migrate actor did:web → did:plc via PDS XRPC com.etzhayyim.plc.migrateActor."""
    from .projector import resolve_pds
    pds_url = (pds or resolve_pds()).rstrip("/")
    resolved_handle = handle or f"{actor}.etzhayyim.com"

    if offline:
        mock = {
            "did": f"did:plc:{actor}aaaaaaaaaaaaaaaaaaaaa"[:32],
            "genesisCid": "bafysimulated000000000000000000000000000",
            "plcUrl": f"https://plc.etzhayyim.com/did:plc:{actor}aaa",
            "handle": resolved_handle,
            "legacyDid": f"did:web:{resolved_handle}",
        }
        if json_out:
            click.echo(json.dumps(mock, indent=2))
        else:
            click.echo(f"  actor:       {actor}")
            click.echo(f"  current DID: did:web:{resolved_handle}")
            click.echo(f"  handle:      {resolved_handle}")
            click.echo(f"  mode:        offline + dry-run (mock response, no write)")
            click.echo(f"\n  ── Response")
            click.echo(f"    new DID:     {mock['did']}")
            click.echo(f"    genesis CID: {mock['genesisCid']}")
        return

    payload = {"actor": actor, "handle": resolved_handle, "dryRun": not apply}
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.plc.migrateActor",
            json=payload,
            headers=_auth_headers(),
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")

    if json_out:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  actor:   {actor}")
        click.echo(f"  new DID: {data.get('did', '?')}")
        click.echo(f"  genesis: {data.get('genesisCid', '?')}")
        if apply:
            click.echo("  deps.toml: update manually with new DID")


@actors.command("cc-coverage")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--graph", default="https://graph.etzhayyim.com", show_default=True, help="graph Worker base URL")
@click.option("--top", default=30, type=int, show_default=True)
@click.option("--topic", default="", help="filter by topic slug (e.g., government, technology)")
@click.option("--min-pages", "min_pages", default=0, type=int, show_default=True)
def actors_cc_coverage(fmt: str, graph: str, top: int, topic: str, min_pages: int) -> None:
    """Common Crawl DID coverage analysis (requires Kotoba/Datomic — use Go binary).

    Queries vertex_domain, vertex_page, edge_hosts_page, edge_links_to_domain
    tables directly via pgxpool. Use the Go binary for full functionality:
      etzhayyim actors cc-coverage [--format text|json] [--top N] [--topic SLUG]
    """
    raise click.ClickException(
        "actors cc-coverage requires direct Kotoba/Datomic access (pgxpool). "
        "Use the Go binary: etzhayyim actors cc-coverage"
    )


@actors.command("common-crawler-coverage")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
@click.option("--graph", default="https://graph.etzhayyim.com")
@click.option("--top", default=30, type=int)
@click.option("--topic", default="")
@click.option("--min-pages", "min_pages", default=0, type=int)
def actors_common_crawler_coverage(fmt: str, graph: str, top: int, topic: str, min_pages: int) -> None:
    """Alias for cc-coverage (requires Kotoba/Datomic — use Go binary)."""
    raise click.ClickException(
        "actors common-crawler-coverage requires direct Kotoba/Datomic access (pgxpool). "
        "Use the Go binary: etzhayyim actors common-crawler-coverage"
    )
