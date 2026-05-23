from typing import TypedDict
from langgraph.graph import StateGraph, END

class EphedrineState(TypedDict):
    batch_id: str
    purity_level: float
    regulatory_clearance: bool

def validate_purity(state: EphedrineState):
    print(f"Validating purity for {state['batch_id']}")
    return {"purity_level": state['purity_level']}

def check_regulations(state: EphedrineState):
    print("Verifying legal compliance and dual-use permits")
    return {"regulatory_clearance": True}

graph = StateGraph(EphedrineState)
graph.add_node("validate", validate_purity)
graph.add_node("compliance", check_regulations)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
