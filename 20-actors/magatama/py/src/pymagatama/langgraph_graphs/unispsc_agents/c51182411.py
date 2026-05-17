from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    batch_id: str
    compliance_cleared: bool
    purity_level: float

def validate_batch(state: ProcessingState):
    print(f"Validating batch: {state['batch_id']}")
    return {"compliance_cleared": state.get("purity_level", 0) >= 99.0}

def route_by_compliance(state: ProcessingState):
    return "approved" if state["compliance_cleared"] else "rejected"

graph = StateGraph(ProcessingState)
graph.add_node("validation", validate_batch)
graph.set_entry_point("validation")
graph.add_conditional_edges("validation", route_by_compliance, {"approved": END, "rejected": END})
graph = graph.compile()