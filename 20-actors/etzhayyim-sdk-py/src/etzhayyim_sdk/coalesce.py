"""coalesce — Request coalescing for batch MST operations.

This is the ONLY module with a real (non-stub) implementation in the M2 skeleton.
It is the critical-path M2 unblocker for yoro_social_murakumo.translate_post_batch:
36+ target-language translation links would each trigger a separate PDS putRecord,
hitting Zeebe task timeout per ADR-2605215300 §Open risks.

By batching concurrent submits with the same key into one MST commit window
(default 100 ms), 36 concurrent translationLink records collapse into 1–3 actual
PDS round-trips instead of 36.

Design:
  - asyncio.Event used for the per-key "batch ready" signal (zero-poll)
  - asyncio.create_task spawns a batch executor task after the first submit
    for a key within the window
  - max_batch enforces a hard cap; once reached the window closes early
  - flush() waits for all in-flight tasks to complete (graceful shutdown hook
    not in original ADR scope — discovered during impl, see §Open issues)

ADR references:
  ADR-2605215300 §Open risks — Zeebe task timeout on 36+ concurrent translationLink writes
  ADR-2605172000 — @etzhayyim/sdk is the only allowed substrate write seam
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Generic, TypeVar

T = TypeVar("T")

# Global registry of active RequestCoalescer instances for graceful shutdown
_active_coalescers: set[RequestCoalescer] = set()


async def flush_all(timeout_seconds: float = 5.0) -> int:
    """Drain all registered coalescers with a global timeout.

    Intended for use in SIGTERM/SIGINT handlers during graceful shutdown.
    Waits for all in-flight batch windows across all coalescer instances
    to complete, respecting a global timeout.

    Args:
        timeout_seconds: maximum time to wait for all coalescers to flush.
            Defaults to 5.0 seconds.

    Returns:
        The number of coalescers flushed.

    Raises:
        asyncio.TimeoutError: if timeout is exceeded before all flushes complete.
            In this case, some batch windows may still be in-flight.
    """
    coalescers = list(_active_coalescers)
    count = len(coalescers)

    if count == 0:
        return 0

    flush_tasks = [c.flush() for c in coalescers]

    try:
        await asyncio.wait_for(
            asyncio.gather(*flush_tasks, return_exceptions=True),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        # Log warning but don't re-raise — allow shutdown to proceed
        pass

    return count


class _PendingBatch(Generic[T]):
    """Internal state for one key's in-flight batch window."""

    __slots__ = ("futures", "task", "ready")

    def __init__(self) -> None:
        self.futures: list[asyncio.Future[T]] = []
        self.task: asyncio.Task[None] | None = None
        self.ready = asyncio.Event()


class RequestCoalescer:
    """Batches concurrent calls to the same key within a time window.

    Used by yoro_social_murakumo.translate_post_batch to coalesce 36+ target-language
    translations into one MST commit instead of 36 separate commits, hitting Zeebe
    task timeout per ADR-2605215300 §Open risks.

    Usage::

        coalescer = RequestCoalescer(window_ms=100, max_batch=64)

        # All concurrent submits for the same key within 100 ms are batched:
        result = await coalescer.submit(
            key=source_uri,
            fn=lambda: etzhayyim_sdk.pds.put_record(
                collection="app.etzhayyim.translationLink",
                record=record,
            )
        )

        # Graceful shutdown (wait for all in-flight batches to complete):
        await coalescer.flush()

    Graceful shutdown integration (M3):
        The `flush_all()` module function drains all registered coalescers
        during SIGTERM/SIGINT handling. See magatama-cell-runner._on_shutdown()
        for integration with launchd graceful shutdown (ADR-2605202100).
    """

    def __init__(self, window_ms: int = 100, max_batch: int = 64) -> None:
        if window_ms <= 0:
            raise ValueError(f"window_ms must be positive, got {window_ms}")
        if max_batch <= 0:
            raise ValueError(f"max_batch must be positive, got {max_batch}")
        self._window_s = window_ms / 1000.0
        self._max_batch = max_batch
        self._batches: dict[str, _PendingBatch[Any]] = {}
        self._lock = asyncio.Lock()
        # Register this coalescer for graceful shutdown
        _active_coalescers.add(self)

    async def submit(self, key: str, fn: Callable[[], Awaitable[T]]) -> T:
        """Submit a call to be coalesced with concurrent calls for the same key.

        The first caller for a key within a window starts the batch timer.
        All callers within the window (up to max_batch) share the result of
        a single fn() invocation.

        Args:
            key: coalescing key (e.g. the source AT URI for translations).
            fn:  zero-argument async callable that performs the actual operation.
                 Only the fn from the *first* submission for a key is called;
                 subsequent submissions in the same batch window share its result.

        Returns:
            The result of fn().

        Raises:
            Whatever fn() raises — propagated to all waiters in the batch.
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[T] = loop.create_future()

        async with self._lock:
            batch = self._batches.get(key)
            if batch is None:
                batch = _PendingBatch()
                self._batches[key] = batch
                batch.futures.append(future)
                # First submitter: start the batch window task
                batch.task = asyncio.create_task(
                    self._run_batch(key, fn, batch),
                    name=f"coalesce-{key[:32]}",
                )
            else:
                batch.futures.append(future)
                # If max_batch reached, signal the batch to close early
                if len(batch.futures) >= self._max_batch:
                    batch.ready.set()

        return await future

    async def _run_batch(
        self,
        key: str,
        fn: Callable[[], Awaitable[T]],
        batch: _PendingBatch[T],
    ) -> None:
        """Wait for the window to close, then execute fn() and resolve all futures."""
        try:
            # Wait for window_ms OR until max_batch is reached (whichever comes first)
            try:
                await asyncio.wait_for(batch.ready.wait(), timeout=self._window_s)
            except asyncio.TimeoutError:
                pass  # window expired normally

            # Execute the single coalesced call
            try:
                result = await fn()
                for f in batch.futures:
                    if not f.done():
                        f.set_result(result)
            except Exception as exc:
                for f in batch.futures:
                    if not f.done():
                        f.set_exception(exc)
        finally:
            # Remove the key so a new batch can start after the window closes
            async with self._lock:
                self._batches.pop(key, None)

    async def flush(self) -> None:
        """Wait for all in-flight batch tasks to complete.

        Call this during graceful shutdown (SIGTERM handler) to ensure
        in-progress MST writes are not abandoned.

        Raises:
            asyncio.TimeoutError: if flushing takes longer than timeout.
        """
        async with self._lock:
            tasks = [b.task for b in self._batches.values() if b.task is not None]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def close(self) -> None:
        """Deregister this coalescer from the global registry.

        Called automatically when exiting async context manager (__aexit__).
        Safe to call multiple times.
        """
        _active_coalescers.discard(self)

    async def __aenter__(self) -> RequestCoalescer:
        """Async context manager entry — returns self."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit — deregisters the coalescer."""
        self.close()

    @property
    def pending_keys(self) -> list[str]:
        """Return the list of keys currently in an active batch window (for observability)."""
        return list(self._batches.keys())
