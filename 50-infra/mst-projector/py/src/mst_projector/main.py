"""mst-projector entry point — M4 deliverable per ADR-2605215500.

Supports concurrent subscriber + XRPC query server via asyncio tasks.

Usage (via uv run / launchd):
    mst-projector --subscribe --serve
    mst-projector --serve --port 9000
    mst-projector --subscribe --cursor-id my-node
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="mst-projector — AT Protocol MST firehose subscriber + XRPC query server",
    )
    parser.add_argument(
        "--subscribe",
        action="store_true",
        help="Run firehose subscriber (writes to LanceDB)",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run XRPC query server",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("ETZHAYYIM_MST_PROJECTOR_HOST", "127.0.0.1"),
        help="Query server bind host (default: 127.0.0.1; env: ETZHAYYIM_MST_PROJECTOR_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ETZHAYYIM_MST_PROJECTOR_PORT", "8765")),
        help="Query server TCP port (default: 8765; env: ETZHAYYIM_MST_PROJECTOR_PORT)",
    )
    parser.add_argument(
        "--cursor-id",
        default="mst-projector-default",
        help="Subscriber cursor identifier for persistent resume (default: mst-projector-default)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    _log = logging.getLogger("mst_projector.main")

    if not args.subscribe and not args.serve:
        _log.error("must specify --subscribe and/or --serve")
        parser.print_usage(sys.stderr)
        return 2

    asyncio.run(_async_main(args))
    return 0


async def _async_main(args: argparse.Namespace) -> None:
    from .query_api import serve as serve_query_api
    from .subscriber import run_subscriber

    _log = logging.getLogger("mst_projector.main")
    tasks: list[asyncio.Task] = []
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_event.set)

    if args.subscribe:
        _log.info("starting subscriber (cursor_id=%r)", args.cursor_id)
        tasks.append(
            asyncio.create_task(
                run_subscriber(cursor_id=args.cursor_id),
                name="subscriber",
            )
        )
    if args.serve:
        _log.info("starting query server on %s:%d", args.host, args.port)
        tasks.append(
            asyncio.create_task(
                serve_query_api(host=args.host, port=args.port),
                name="query_api",
            )
        )

    # Wait for any task to complete OR stop signal
    done, pending = await asyncio.wait(
        [*tasks, asyncio.create_task(stop_event.wait(), name="stop_event")],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Log any unexpected task failure
    for task in done:
        if task.get_name() != "stop_event":
            exc = task.exception() if not task.cancelled() else None
            if exc is not None:
                _log.error("task %r raised: %s", task.get_name(), exc)

    # Cancel remaining tasks and wait for cleanup
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    _log.info("mst-projector shut down cleanly")


if __name__ == "__main__":
    sys.exit(main())
