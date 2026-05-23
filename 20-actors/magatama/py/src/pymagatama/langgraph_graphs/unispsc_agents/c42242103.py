from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TractionState(TypedDict):
    material: str
    quality_check_required: bool
    compliance_docs: List[str]

def validate_traction_specs(state: TractionState):
    if not state.get("compliance_docs"):
        return {"quality_check_required": True}
    return {"quality_check_required": False}

def process_procurement(state: TractionState):
    print(f"Processing traction supplies: {state['material']}")
    return state

graph = StateGraph(TractionState)
graph.add_node("validate", validate_traction_specs)
graph.add_node("process", process_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
compiled_graph = graph.compile()
