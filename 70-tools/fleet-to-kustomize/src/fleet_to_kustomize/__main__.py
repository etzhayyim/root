"""CLI for fleet-to-kustomize."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from ruamel.yaml import YAML

from .generator import (
    IMAGE_DEFAULT,
    NAMESPACE_DEFAULT,
    Placement,
    kebab,
    load_fleet,
    render_cell_kustomization,
    render_daemonset,
    render_namespace,
    render_root_kustomization,
    render_service,
    render_serviceaccount,
    resolve_placements,
)


def _yaml() -> YAML:
    y = YAML()
    y.default_flow_style = False
    y.indent(mapping=2, sequence=4, offset=2)
    y.width = 120
    return y


def _write_yaml(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        _yaml().dump(doc, f)


@click.command()
@click.option(
    "--fleet",
    "fleet_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path("50-infra/murakumo/fleet.toml"),
    show_default=True,
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("50-infra/k8s/murakumo"),
    show_default=True,
)
@click.option(
    "--cell",
    "only_cells",
    multiple=True,
    help="Limit emission to one or more cell names (CamelCase). Repeatable.",
)
@click.option(
    "--target",
    type=click.Choice(["production", "orbstack"]),
    default="production",
    show_default=True,
    help="`orbstack` overrides nodeSelector to kubernetes.io/hostname=orbstack for local single-node validation.",
)
@click.option(
    "--repo-hostpath",
    default=None,
    help=(
        "Mount this host directory at /repo (orbstack only). Lets cell_runner_main.py "
        "resolve fleet.toml + cell modules from the live repo. Auto-defaulted to "
        "the repo containing fleet.toml when --target orbstack."
    ),
)
@click.option(
    "--image",
    default=IMAGE_DEFAULT,
    show_default=True,
)
@click.option(
    "--namespace",
    default=NAMESPACE_DEFAULT,
    show_default=True,
)
@click.option(
    "--dry-run/--write",
    default=False,
    help="`--dry-run` prints the generated cell names and would-be paths without writing.",
)
def main(
    fleet_path: Path,
    out_dir: Path,
    only_cells: tuple[str, ...],
    target: str,
    repo_hostpath: str | None,
    image: str,
    namespace: str,
    dry_run: bool,
) -> None:
    """Project fleet.toml → k3s DaemonSet kustomize overlay per ADR-2605232100."""
    fleet = load_fleet(fleet_path)
    all_placements, warnings = resolve_placements(fleet)
    if target == "orbstack" and repo_hostpath is None:
        # Auto-resolve to the repo root holding fleet.toml.
        repo_hostpath = str(fleet_path.resolve().parents[2])

    for w in warnings:
        click.echo(f"warn: {w}", err=True)

    if only_cells:
        wanted = set(only_cells)
        placements = [p for p in all_placements if p.cell_name in wanted]
        missing = wanted - {p.cell_name for p in placements}
        if missing:
            click.echo(
                f"error: cells not found (or shard-deferred) in fleet.toml: {sorted(missing)}",
                err=True,
            )
            sys.exit(2)
    else:
        placements = all_placements

    target_hostname = "orbstack" if target == "orbstack" else None
    cell_names = [p.cell_name for p in placements]

    if dry_run:
        click.echo(f"fleet: {fleet_path}")
        click.echo(f"out:   {out_dir}")
        click.echo(f"target: {target} (override hostname={target_hostname!r})")
        click.echo(f"image: {image}")
        click.echo(f"namespace: {namespace}")
        click.echo(f"cells ({len(placements)}):")
        for p in placements:
            click.echo(
                f"  - {p.cell_name:>35s} on {p.leader_node:>10s} "
                f"(healthz :{p.healthz_port}, trigger={p.trigger!r})"
            )
        return

    # Root kustomization + namespace.
    _write_yaml(out_dir / "kustomization.yaml", render_root_kustomization(cell_names, namespace))
    _write_yaml(out_dir / "namespace.yaml", render_namespace(namespace))

    # Per-cell overlay.
    for p in placements:
        cell_dir = out_dir / "cells" / kebab(p.cell_name)
        _write_yaml(cell_dir / "kustomization.yaml", render_cell_kustomization(p, namespace))
        _write_yaml(cell_dir / "serviceaccount.yaml", render_serviceaccount(p, namespace))
        _write_yaml(cell_dir / "service.yaml", render_service(p, namespace))
        _write_yaml(
            cell_dir / "daemonset.yaml",
            render_daemonset(p, namespace, image, target_hostname, repo_hostpath),
        )

    click.echo(f"emitted {len(placements)} cell(s) → {out_dir}/")
    for p in placements:
        click.echo(f"  - cells/{kebab(p.cell_name)}/   (leader={p.leader_node}, healthz=:{p.healthz_port})")


if __name__ == "__main__":
    main()
