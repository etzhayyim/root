#!/usr/bin/env python3
"""deploy_node — codified per-node deploy of the lite cell-runner (ADR-2606161645).

Stages the pure-stdlib supervisor + cells.edn + every actor assigned to a node (resolved FROM
cells.edn) to `<home>/.etzhayyim/`, then installs the ONE system LaunchDaemon (sudo). This is the
reproducible form of the manual `git archive | ssh | sudo launchctl bootstrap` deploy. Uses
Tailscale SSH (resolve IP from `tailscale status`) + passwordless sudo on the node.

The plan is a pure function (testable offline); the network/sudo legs are an INJECTED runner.

    python3 deploy_node.py --node issachar --dry-run     # print the plan
    python3 deploy_node.py --node issachar               # stage + install (needs ssh + sudo)
"""
from __future__ import annotations
import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lite_runner as lr  # reuse the EDN reader + load_cells  # noqa: E402

REGISTRY = HERE / "cells.edn"
ACTOR_SOURCES = HERE / "actor-sources.edn"
DAEMON_TPL = HERE / "com.etzhayyim.cell-runner.daemon.plist"


def actors_for_node(registry, node):
    """The set of actor names (module prefix before '.') for a node's cron cells in cells.edn."""
    actors = []
    for c in lr.load_cells(registry, node):
        mod = c.get(":module", "")
        actor = mod.split(".", 1)[0]
        if actor and actor not in actors:
            actors.append(actor)
    return actors


def actor_source(actor, sources=ACTOR_SOURCES):
    """Resolve an actor to its canonical flat-west checkout, with a migration fallback."""
    doc = lr.parse_edn(pathlib.Path(sources).read_text(encoding="utf-8"))
    source = doc.get(":actor-sources", {}).get(actor)
    if source:
        return source
    fallback = dict(doc[":default"])
    fallback[":path"] = fallback[":path-template"].replace("{actor}", actor)
    return fallback


def plan(node, registry=REGISTRY):
    """Pure: the ordered deploy actions for a node (what deploy() will execute)."""
    actors = actors_for_node(registry, node)
    steps = [("mkdirs", f"~/.etzhayyim/{{cells,log}}"),
             ("stage", "lite_runner.cljc → ~/.etzhayyim/lite_runner.cljc (the bb runner; ADR-2606221900)"),
             ("stage", "lite_runner.py → ~/.etzhayyim/lite_runner.py (rollback runner)"),
             ("stage", "cells.edn → ~/.etzhayyim/cells.edn")]
    for a in actors:
        steps.append(("stage-actor", f"{actor_source(a)[':path']} → ~/.etzhayyim/cells/{a}"))
    steps.append(("install-daemon", "com.etzhayyim.cell-runner (system LaunchDaemon, sudo, KeepAlive)"))
    return {"node": node, "actors": actors, "steps": steps}


def _tailscale_ip(node, status_text=None):
    txt = status_text if status_text is not None else \
        subprocess.run(["tailscale", "status"], capture_output=True, text=True, timeout=20).stdout
    return lr_parse_status(txt).get(node)


def lr_parse_status(txt):
    import re
    out = {}
    for line in txt.splitlines():
        p = line.split()
        if len(p) >= 2 and re.match(r"^\d+\.\d+\.\d+\.\d+$", p[0]):
            out[p[1]] = p[0]
    return out


def deploy(node, *, registry=REGISTRY, daemon_tpl=DAEMON_TPL, ref="origin/main", runner=None,
           ip=None, status_text=None, bb_path="/opt/homebrew/bin/bb"):
    """Execute the plan. runner(kind, **kw) is INJECTED in tests; default does git+ssh+sudo.

    Cutover (ADR-2606221900): stages BOTH lite_runner.cljc (the bb runner the plist invokes) and
    lite_runner.py (the rollback runner), and substitutes @@BB_PATH@@ in the daemon plist with the
    node's absolute bb path (launchd's minimal PATH makes a bare `bb` exit 127). `bb_path` defaults
    to the Apple-silicon homebrew location (the fleet Mac minis); override with --bb-path.
    """
    pl = plan(node, registry)
    ip = ip or _tailscale_ip(node, status_text)
    if not ip:
        return {"node": node, "status": "unreachable", "plan": pl}
    home = f"/Users/{node}"
    r = runner or _default_runner
    r("mkdirs", node=node, ip=ip, cmd=f"mkdir -p {home}/.etzhayyim/cells {home}/.etzhayyim/log")
    r("put-file", node=node, ip=ip, local=str(HERE / "lite_runner.cljc"),
      remote=f"{home}/.etzhayyim/lite_runner.cljc")
    r("put-file", node=node, ip=ip, local=str(HERE / "lite_runner.py"),
      remote=f"{home}/.etzhayyim/lite_runner.py")
    r("put-file", node=node, ip=ip, local=str(ACTOR_SOURCES),
      remote=f"{home}/.etzhayyim/actor-sources.edn")
    r("git-show", node=node, ip=ip, ref=ref,
      path="50-infra/cluster/murakumo/cell-runner/cells.edn", remote=f"{home}/.etzhayyim/cells.edn")
    for a in pl["actors"]:
        source = actor_source(a)
        if source[":kind"] == ":west-repository":
            r("git-archive-repo", node=node, ip=ip, repository=source[":path"],
              revision=source[":revision"], remote=f"{home}/.etzhayyim/cells/{a}")
        else:
            r("git-archive", node=node, ip=ip, ref=ref, path=source[":path"],
              remote=f"{home}/.etzhayyim/cells/{a}", strip=2)
    plist = daemon_tpl.read_text(encoding="utf-8").replace("@@USER@@", node) \
        .replace("@@HOME@@", home).replace("@@NODE@@", node).replace("@@BB_PATH@@", bb_path)
    r("install-daemon", node=node, ip=ip, plist=plist, label="com.etzhayyim.cell-runner")
    return {"node": node, "status": "deployed", "plan": pl, "ip": ip, "bb_path": bb_path}


def _ssh(ip, node, cmd, stdin=None):
    return subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
                           "-o", "StrictHostKeyChecking=accept-new", f"{node}@{ip}", cmd],
                          input=stdin, capture_output=True, timeout=120)


def _default_runner(kind, **kw):
    node, ip = kw["node"], kw["ip"]
    if kind == "mkdirs":
        _ssh(ip, node, kw["cmd"])
    elif kind == "put-file":
        _ssh(ip, node, f'cat > {kw["remote"]}', stdin=pathlib.Path(kw["local"]).read_bytes())
    elif kind == "git-show":
        data = subprocess.run(["git", "show", f'{kw["ref"]}:{kw["path"]}'],
                              capture_output=True, timeout=60).stdout
        _ssh(ip, node, f'cat > {kw["remote"]}', stdin=data)
    elif kind == "git-archive":
        data = subprocess.run(["git", "archive", kw["ref"], kw["path"]],
                              capture_output=True, timeout=60).stdout
        _ssh(ip, node, f'rm -rf {kw["remote"]} && mkdir -p {kw["remote"]} && '
                       f'tar -C {kw["remote"]} --strip-components={kw["strip"]} -xf -', stdin=data)
    elif kind == "git-archive-repo":
        data = subprocess.run(["git", "-C", kw["repository"], "archive", kw["revision"]],
                              capture_output=True, timeout=60, check=True).stdout
        _ssh(ip, node, f'rm -rf {kw["remote"]} && mkdir -p {kw["remote"]} && '
                       f'tar -C {kw["remote"]} -xf -', stdin=data)
    elif kind == "install-daemon":
        lbl = kw["label"]
        _ssh(ip, node, f'cat > /tmp/{lbl}.plist && '
                       f'sudo launchctl bootout system/{lbl} 2>/dev/null; '
                       f'sudo cp /tmp/{lbl}.plist /Library/LaunchDaemons/{lbl}.plist && '
                       f'sudo chown root:wheel /Library/LaunchDaemons/{lbl}.plist && '
                       f'sudo launchctl bootstrap system /Library/LaunchDaemons/{lbl}.plist',
             stdin=kw["plist"].encode())


def main(argv):
    ap = argparse.ArgumentParser(description="deploy the lite cell-runner to a fleet node")
    ap.add_argument("--node", required=True)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--bb-path", default="/opt/homebrew/bin/bb",
                    help="absolute path to bb on the node (launchd needs an abs path; default = Apple-silicon brew)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.dry_run:
        pl = plan(a.node)
        print(f"deploy plan for {a.node} (actors: {', '.join(pl['actors']) or 'none'}):")
        for k, d in pl["steps"]:
            print(f"  [{k}] {d}")
        return 0
    res = deploy(a.node, ref=a.ref, bb_path=a.bb_path)
    print(f"deploy_node {a.node}: {res['status']}"
          + (f" (actors: {', '.join(res['plan']['actors'])})" if res.get("plan") else ""))
    return 0 if res["status"] == "deployed" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
