;; ported from 60-apps/etzhayyim-project-animeka/lg/lg_animeka/checkpointer.py (unit_refactor stage 0)
;; RisingWave-compatible LangGraph checkpoint saver.
(ns etzhayyim-project-animeka.lg.lg-animeka.checkpointer
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare log build-checkpointer)

;; TODO: port-failed unit _log (assembled-lint error)
;; _log = logging.getLogger(__name__)
;; CHECKPOINTER_URL = os.environ.get("LG_CHECKPOINTER_URL") or os.environ.get("RW_URL", "")
;; _RW_INSERT_CHECKPOINT = """
;;     INSERT INTO lg_checkpoints
;;         (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
;;          type, checkpoint, metadata, created_at)
;;     VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
;; """
;; _RW_INSERT_BLOB = """
;;     INSERT INTO lg_checkpoint_blobs
;;         (thread_id, checkpoint_ns, channel, version, type, blob, created_at)
;;     VALUES (%s, %s, %s, %s, %s, %s, NOW())
;; """
;; _RW_DELETE_WRITES = """
;;     DELETE FROM lg_checkpoint_writes
;;     WHERE thread_id = %s
;;       AND checkpoint_ns = %s
;;       AND checkpoint_id = %s
;;       AND task_id = %s
;;       AND idx = %s
;; """
;; _RW_INSERT_WRITES = """
;;     INSERT INTO lg_checkpoint_writes
;;         (thread_id, checkpoint_ns, checkpoint_id, task_id, idx,
;;          channel, type, blob, task_path, created_at)
;;     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
;; """
(def log nil) ;; TODO: port-failed const

;; TODO: port-failed unit build_checkpointer (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp1voy1t25/scratch.clj:2:1: er)
;; async def build_checkpointer() -> AsyncIterator[Any]:
;;     """Yield a LangGraph checkpoint saver bound to RW PG.
;; 
;;     Strategy: subclass `AsyncPostgresSaver` and override the three
;;     write methods to use RW-compat SQL. Reads (`aget_tuple`, `alist`)
;;     are unmodified — they're plain SELECTs that work as-is on RW.
;;     """
;;     from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
;;     from langgraph.checkpoint.base import (
;;         Checkpoint,
;;         CheckpointMetadata,
;;         CheckpointTuple,
;;         copy_checkpoint,
;;     )
;;     from langgraph.checkpoint.serde.types import TASKS
;; 
;;     if not CHECKPOINTER_URL:
;;         raise RuntimeError(
;;             "LG_CHECKPOINTER_URL or RW_URL must be set "
;;             "for the lg-animeka checkpointer"
;;         )
;; 
;;     class _RwAsyncPostgresSaver(AsyncPostgresSaver):
;;         async def setup(self) -> None:
;;             # The migration creates the tables and seeds
;;             # `lg_checkpoint_migrations`; setup() becomes a no-op.
;;             return
;; 
;;         async def aput(
;;             self,
;;             config: dict,
;;             checkpoint: "Checkpoint",
;;             metadata: "CheckpointMetadata",
;;             new_versions: dict,
;;         ) -> dict:
;;             """RW-compat: PK-implicit overwrite, no ON CONFLICT."""
;;             cfg = config["configurable"]
;;             thread_id = cfg["thread_id"]
;;             checkpoint_ns = cfg.get("checkpoint_ns", "")
;;             checkpoint_id = checkpoint["id"]
;;             parent_id = cfg.get("checkpoint_id")
;;             ckpt_blob = self.serde.dumps(copy_checkpoint(checkpoint))
;;             meta_blob = self.serde.dumps(metadata)
;; 
;;             async with self._cursor() as cur:  # type: ignore[attr-defined]
;;                 # Channel-value blobs first, so a partial failure leaves
;;                 # the parent checkpoint pointing at incomplete blobs
;;                 # (LangGraph's invariant).
;;                 for channel, version in new_versions.items():
;;                     val = checkpoint["channel_values"].get(channel)
;;                     val_type, val_blob = (
;;                         ("empty", b"") if val is None else self.serde.dumps_typed(val)
;;                     )
;;                     await cur.execute(
;;                         _RW_INSERT_BLOB,
;;                         (
;;                             thread_id, checkpoint_ns, channel, str(version),
;;                             val_type, val_blob,
;;                         ),
;;                     )
;; 
;;                 await cur.execute(
;;                     _RW_INSERT_CHECKPOINT,
;;                     (
;;                         thread_id, checkpoint_ns, checkpoint_id, parent_id,
;;                         "msgpack", ckpt_blob, meta_blob,
;;                     ),
;;                 )
;; 
;;             return {
;;                 "configurable": {
;;                     "thread_id": thread_id,
;;                     "checkpoint_ns": checkpoint_ns,
;;                     "checkpoint_id": checkpoint_id,
;;                 }
;;             }
;; 
;;         async def aput_writes(
;;             self,
;;             config: dict,
;;             writes: list,
;;             task_id: str,
;;             task_path: str = "",
;;         ) -> None:
;;             """RW-compat: delete-then-insert (no INSERT ... DO NOTHING)."""
;;             cfg = config["configurable"]
;;             thread_id = cfg["thread_id"]
;;             checkpoint_ns = cfg.get("checkpoint_ns", "")
;;             checkpoint_id = cfg["checkpoint_id"]
;; 
;;             async with self._cursor() as cur:  # type: ignore[attr-defined]
;;                 for idx, (channel, value) in enumerate(writes):
;;                     val_type, val_blob = self.serde.dumps_typed(value)
;;                     await cur.execute(
;;                         _RW_DELETE_WRITES,
;;                         (thread_id, checkpoint_ns, checkpoint_id, task_id, idx),
;;                     )
;;                     await cur.execute(
;;                         _RW_INSERT_WRITES,
;;                         (
;;                             thread_id, checkpoint_ns, checkpoint_id, task_id, idx,
;;                             channel, val_type, val_blob, task_path,
;;                         ),
;;                     )
;; 
;;     async with _RwAsyncPostgresSaver.from_conn_string(CHECKPOINTER_URL) as cp:
;;         # `setup()` is a no-op on this subclass; tables come from
;;         # the Kysely migration.
;;         yield cp
(defn build-checkpointer [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_checkpointer"})))

