from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperSheetState(TypedDict):
    alloy_type: str
    thickness: float
    certification_verified: bool

def validate_specs(state: CopperSheetState):
    print(f"Validating copper sheet: {state['alloy_type']} at {state['thickness']}mm")
    return {"certification_verified": state['thickness'] > 0}

def approval_node(state: CopperSheetState):
    return {"certification_verified": True}

graph = StateGraph(CopperSheetState)
graph.add_node("validate", validate_specs)
graph.add_node("approve", approval_node)
graph.set_entry_point("validate")
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph = graph.compile()