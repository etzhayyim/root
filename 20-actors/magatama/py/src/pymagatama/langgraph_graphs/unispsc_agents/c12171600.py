from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class CatalystState(TypedDict):
    material_id: str
    purity: float
    safety_clearance: bool
    history: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystState) -> CatalystState:
    return {"history": ["Validating purity requirement"], "safety_clearance": state["purity"] >= 99.9}

def check_regulations(state: CatalystState) -> CatalystState:
    return {"history": ["Checking export control compliance"], "safety_clearance": state["safety_clearance"] and True}

graph = StateGraph(CatalystState)
graph.add_node("validate", validate_purity)
graph.add_node("compliance", check_regulations)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
app = graph.compile()