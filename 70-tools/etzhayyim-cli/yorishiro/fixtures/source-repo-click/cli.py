"""Fixture Click app for the yorishiro source-repo extractor tests.

Run the extractor against this directory to produce a kami manifest:

    python3 70-tools/etzhayyim-cli/yorishiro/scripts/extract-click.py \\
        70-tools/etzhayyim-cli/yorishiro/fixtures/source-repo-click \\
        --kami-id bin:demo-fixture --binary demo-fixture
"""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Demo Click CLI used by the yorishiro source-repo fixture."""


@cli.command()
@click.argument("name")
@click.option("--shout", is_flag=True, help="Uppercase the greeting.")
@click.option("--lang", default="en", help="Language code (en|jp).")
def greet(name: str, shout: bool, lang: str) -> None:
    """Print a greeting for NAME."""
    greeting = {"en": "Hello", "jp": "konnichiwa"}.get(lang, "Hello")
    msg = f"{greeting}, {name}!"
    click.echo(msg.upper() if shout else msg)


@cli.command()
@click.argument("input_path")
@click.argument("output_path", required=False, default="-")
@click.option("--max-lines", "max_lines", type=int, default=100, help="Maximum lines to read.")
@click.option("--encoding", default="utf-8", help="Input encoding.")
def head(input_path: str, output_path: str, max_lines: int, encoding: str) -> None:
    """Read up to MAX_LINES from INPUT_PATH and write to OUTPUT_PATH."""
    with open(input_path, encoding=encoding) as f:
        lines = []
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line)
    out = "".join(lines)
    if output_path == "-":
        click.echo(out, nl=False)
    else:
        with open(output_path, "w", encoding=encoding) as o:
            o.write(out)


if __name__ == "__main__":
    cli()
