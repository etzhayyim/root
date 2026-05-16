import uuid
import json
import time
from typing import Any, Dict, List, Optional
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from pymagatama.db_sync import sync_cursor

class LangProcessMinerCallbackHandler(BaseCallbackHandler):
    def __init__(self, agent_role: str, run_name: str, owner_did: str = "did:web:malak.gftd.ai"):
        self.agent_role = agent_role
        self.run_name = run_name
        self.owner_did = owner_did
        self.trace_id = f"trace-{uuid.uuid4().hex}"
        self.spans = {}
        
        # Start trace
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        now_date = time.strftime("%Y-%m-%d", time.gmtime())
        self.trace_start_time = now
        self.trace_date = now_date
        
        self.vertex_id = f"at://did:web:malak.gftd.ai/ai.gftd.apps.lpm.trace/{self.trace_id}"
        
        try:
            with sync_cursor() as cur:
                cur.execute("""
                    INSERT INTO vertex_langprocessminer_trace
                    (vertex_id, rkey, repo, trace_id, agent_role, run_name, start_time, status, created_date, owner_did)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.vertex_id,
                    self.trace_id,
                    self.owner_did,
                    self.trace_id,
                    self.agent_role,
                    self.run_name,
                    self.trace_start_time,
                    "running",
                    self.trace_date,
                    self.owner_did
                ))
        except Exception as e:
            print(f"[LPM Error] Failed to start trace: {e}")

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        span_id = str(run_id)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.spans[span_id] = {"start_time": now}
        
        vertex_id = f"at://{self.owner_did}/ai.gftd.apps.lpm.span/{span_id}"
        try:
            with sync_cursor() as cur:
                cur.execute("""
                    INSERT INTO vertex_langprocessminer_span
                    (vertex_id, rkey, repo, span_id, trace_id, node_name, span_kind, input_json, start_time, created_date, owner_did)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    vertex_id,
                    span_id,
                    self.owner_did,
                    span_id,
                    self.trace_id,
                    "llm_call",
                    "llm",
                    json.dumps(prompts),
                    now,
                    self.trace_date,
                    self.owner_did
                ))
        except Exception as e:
            print(f"[LPM Error] Failed to start span: {e}")

    def on_llm_end(self, response: LLMResult, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any) -> Any:
        span_id = str(run_id)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Extract token usage if available
        prompt_tokens = 0
        completion_tokens = 0
        if response.llm_output and "token_usage" in response.llm_output:
            prompt_tokens = response.llm_output["token_usage"].get("prompt_tokens", 0)
            completion_tokens = response.llm_output["token_usage"].get("completion_tokens", 0)
            
        try:
            with sync_cursor() as cur:
                cur.execute("""
                    UPDATE vertex_langprocessminer_span
                    SET end_time = %s, output_json = %s, prompt_tokens = %s, completion_tokens = %s
                    WHERE span_id = %s
                """, (
                    now,
                    json.dumps([[g.text for g in gen] for gen in response.generations]),
                    prompt_tokens,
                    completion_tokens,
                    span_id
                ))
                
                # Update total tokens in trace
                cur.execute("""
                    UPDATE vertex_langprocessminer_trace
                    SET total_tokens = total_tokens + %s + %s
                    WHERE trace_id = %s
                """, (prompt_tokens, completion_tokens, self.trace_id))
        except Exception as e:
            print(f"[LPM Error] Failed to end span: {e}")

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        # Simplified: We could track every chain/graph node, but for now we'll just track LLM calls as spans.
        pass

    def conclude_trace(self, status: str = "success", final_output: Any = None):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            with sync_cursor() as cur:
                cur.execute("""
                    UPDATE vertex_langprocessminer_trace
                    SET end_time = %s, status = %s, output_json = %s
                    WHERE trace_id = %s
                """, (
                    now,
                    status,
                    json.dumps(final_output) if final_output else None,
                    self.trace_id
                ))
        except Exception as e:
            print(f"[LPM Error] Failed to conclude trace: {e}")
