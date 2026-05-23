from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PurificationState(TypedDict):
    sample_id: str
    purity_level: float
    storage_temp: float
    validation_status: str

def validate_purity(state: PurificationState):
    print(f'Validating purity for {state["sample_id"]}')
    return {"validation_status": "PASS" if state["purity_level"] > 0.95 else "FAIL"}

def check_cold_chain(state: PurificationState):
    print(f'Checking cold chain at {state["storage_temp"]}C')
    return {"validation_status": "FAIL" if state["storage_temp"] > -20 else state["validation_status"]}

graph = StateGraph(PurificationState)
graph.add_node("validate", validate_purity)
graph.add_node("cold_chain", check_cold_chain)
graph.set_entry_point("validate")
graph.add_edge("validate", "cold_chain")
graph.add_edge("cold_chain", END)
graph = graph.compile()
