"""etzhayyim CLI entry point — Python port (ADR-2605151500).

Commands are ported incrementally. Unported commands print a message directing
to the Go binary.
"""

import sys
import click

from .actors import actors
from .agent_cmd import agent
from .agent_runtime import agent_runtime
from .agent_token import agent_token
from .apps import apps
from .authn import authn
from .authz import authz
from .bonsai import bonsai
from .bunseki import bunseki
from .cohort import cohort
from .code_quality import code_quality_cmd
from .complex_stubs import (
    code,
    collect, common_crawler,
    docs, docs_gen, domain_ingest,
    migrate_manifest, performance_test, plugin,
    pds as _pds_cmd,
    seed, set_profiles, version_cmd,
)
from .process_mining import process_mining as process_mining_cmd
from .hinshitsu import hinshitsu as hinshitsu_cmd
from .coverage import coverage
from .database import database
from .deps import deps
from .deploy import build, deploy
from .dns_sync import dns_sync
from .dodaf import dodaf
from .haisen import haisen
from .identifier_audit import identifier_audit
from .identity import identity
from .kagami import kagami
from .kaizen import kaizen
from .kashika import kashika
from .kosei import kosei
# .lint retired (ADR-2606222000): ported to etzhayyim.lint.cljc → `bb e7m lint`.
from .logs import logs
from .metrics import metrics
from .mitama import mitama
from .mokuteki import mokuteki
from .monitor import monitor
from .murakumo_cmd import murakumo
from .nono import nono
from .organism import organism
from .projector import projector
from .shannon import shannon
from .source_graph import source_graph
from .systemofsystem import systemofsystem
from .training import training
from .vertex import vertex
from .workspace import workspace
from .xrpc import xrpc
from .yoroshiku import yoroshiku


@click.group()
def main():
    """etzhayyim — platform CLI (Python port, parallel with Go binary)."""


# --- all ported commands ------------------------------------------------------
main.add_command(actors)
main.add_command(agent)
main.add_command(agent_runtime)
main.add_command(agent_token)
main.add_command(apps)
main.add_command(authn)
main.add_command(authz)
main.add_command(bonsai)
main.add_command(build)
main.add_command(bunseki)
main.add_command(code)
main.add_command(code_quality_cmd, name="code-quality")
main.add_command(cohort)
main.add_command(collect)
main.add_command(common_crawler, name="common-crawler")
main.add_command(coverage)
main.add_command(coverage, name="coverage-test")  # alias: etzhayyim coverage-test = etzhayyim coverage test
main.add_command(database)
main.add_command(deps)
main.add_command(deploy)
main.add_command(dns_sync)
main.add_command(docs)
main.add_command(docs_gen, name="docs-gen")
main.add_command(dodaf)
main.add_command(domain_ingest, name="domain-ingest")
main.add_command(haisen)
main.add_command(hinshitsu_cmd, name="hinshitsu")
main.add_command(identifier_audit)
main.add_command(identity)
main.add_command(kagami)
main.add_command(kaizen)
main.add_command(kashika)
main.add_command(kosei)
main.add_command(logs)
main.add_command(metrics)
main.add_command(migrate_manifest, name="migrate-manifest")
main.add_command(mitama)
main.add_command(mokuteki)
main.add_command(monitor)
main.add_command(murakumo)
main.add_command(nono)
main.add_command(organism)
main.add_command(performance_test, name="performance-test")
main.add_command(plugin)
main.add_command(process_mining_cmd, name="process-mining")
main.add_command(_pds_cmd, name="pds")
main.add_command(projector)
main.add_command(seed)
main.add_command(set_profiles, name="set-profiles")
main.add_command(shannon)
main.add_command(source_graph)
main.add_command(systemofsystem)
main.add_command(training)
main.add_command(version_cmd, name="version")
main.add_command(vertex)
main.add_command(workspace)
main.add_command(xrpc)
main.add_command(yoroshiku)
