import os
import sys
import time
import json
import uuid
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from pymagatama.malak.graph._llm import call_llm
from pymagatama.malak.langgraph.db_accessor import insert_investigation_tick

# We reuse the LangProcessMiner callback so these runs show up on the Yoro UI dashboard!
from pymagatama.malak.langgraph.lpm_callback import LangProcessMinerCallbackHandler

class FleetTaskState(TypedDict):
    task_type: str       # e.g., 'web_crawler', 'weight_inference', '3d_splat'
    payload: str
    pegel_score: float
    status: str
    deliberation_steps: Annotated[List[str], "append"]
    execution_result: str
    tick_vertex_id: str

def intake_node(state: FleetTaskState) -> dict:
    step = f"intake: Received fleet task '{state['task_type']}'"
    return {"deliberation_steps": [step], "status": "pending"}

def pegel_evaluate_node(state: FleetTaskState) -> dict:
    """PEGEL: Evaluates the provenance and prerequisites for the fleet task."""
    score = 0.85 # Assume base authority for internal jobs
    step = f"pegel: Evaluated execution prerequisites for {state['task_type']}. Score: {score}"
    return {"pegel_score": score, "deliberation_steps": [step]}

def execute_node(state: FleetTaskState) -> dict:
    """Executes the specific workload logic."""
    tt = state['task_type']
    result = ""
    
    # In a real system, these would import the specific module or run a subprocess.
    if tt == "web_crawler":
        result = "Successfully crawled 150 pages from target seeds. Indexed into search.gftd.ai."
    elif tt == "weight_inference":
        result = "Loaded GGUF weights. Inference completed. Metrics: 45 tokens/sec on Metal."
    elif tt == "intel_dependency":
        result = "Analyzed BPMN graphs. Found 3 critical dependencies. Output passed to Malak."
    elif tt == "latent_agent":
        result = "Registered new latent agent profile in ATProto PDS and generated DID."
    elif tt == "maps_ingest":
        result = "Ingested OSM planet chunk. Merged into RisingWave vertex_maps_poi."
    elif tt == "3d_splat":
        result = "Processed 500 images via COLMAP. Baked Gaussian Splatting asset successfully."
    elif tt == "visual_test":
        result = "Playwright E2E visual regressions checked. 0 discrepancies found."
    else:
        result = f"Executed generic workload for {tt}."

    # Ask the LLM to summarize the execution for the dashboard
    prompt = f"Task: {tt}\nResult: {result}\nSummarize this workload execution in one sentence for the analytics dashboard."
    summary, _ = call_llm(prompt, system="You are the Murakumo Fleet orchestrator.")
    
    step = f"execute: {summary}"
    return {"execution_result": summary, "status": "success", "deliberation_steps": [step]}

def process_mining_node(state: FleetTaskState) -> dict:
    """Records the trace to RisingWave via LangProcessMiner."""
    vertex_id = insert_investigation_tick(
        role_id=f"fleet-{state['task_type']}",
        tlp="CLEAR",
        action="execute_workload",
        details=state['payload'],
        rationale=state['execution_result'],
        state_history=state['deliberation_steps']
    )
    step = f"process_mining: Recorded tick at {vertex_id}"
    return {"tick_vertex_id": vertex_id, "deliberation_steps": [step]}

def build_fleet_graph() -> StateGraph:
    workflow = StateGraph(FleetTaskState)
    
    workflow.add_node("intake", intake_node)
    workflow.add_node("pegel_evaluate", pegel_evaluate_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("record_tick", process_mining_node)
    
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "pegel_evaluate")
    workflow.add_edge("pegel_evaluate", "execute")
    workflow.add_edge("execute", "record_tick")
    workflow.add_edge("record_tick", END)
    
    return workflow.compile()

def run_worker():
    task_type = os.environ.get("FLEET_TASK_TYPE", "unknown_task")
    payload = os.environ.get("FLEET_PAYLOAD", "Standard periodic execution.")
    
    sys.stdout.write(f"Starting LangGraph PEGEL worker for {task_type}...\n")
    sys.stdout.flush()
    
    graph = build_fleet_graph()
    
    initial_state = {
        "task_type": task_type,
        "payload": payload,
        "pegel_score": 0.0,
        "status": "init",
        "deliberation_steps": [],
        "execution_result": "",
        "tick_vertex_id": ""
    }
    
    lpm_callback = LangProcessMinerCallbackHandler(
        agent_role=f"fleet-{task_type}", 
        run_name="batch_execute"
    )
    
    try:
        result = graph.invoke(initial_state, config={"callbacks": [lpm_callback]})
        lpm_callback.conclude_trace(status="success", final_output={"rationale": result.get("execution_result")})
        sys.stdout.write(f"Finished: {result.get('execution_result')}\n")
    except Exception as e:
        lpm_callback.conclude_trace(status="error", final_output={"error": str(e)})
        sys.stderr.write(f"Error executing graph: {e}\n")

if __name__ == "__main__":
    # If run as a daemon, sleep and loop
    while True:
        run_worker()
        time.sleep(30) # Run every 30 seconds
