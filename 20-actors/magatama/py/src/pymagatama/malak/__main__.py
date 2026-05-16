"""Entry: `python -m pymagatama.malak [--socket [PATH]]`."""

from __future__ import annotations

import asyncio
import sys

from .lsp_server import main

if __name__ == "__main__":
    asyncio.run(main(sys.argv))
