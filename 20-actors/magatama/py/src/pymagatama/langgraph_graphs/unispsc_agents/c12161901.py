from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity: float
    surface_area: float
    is_compliant: bool
    history: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystState) -> CatalystState:
    return {"is_compliant": state["purity"] >= 99.5, "history": ["Purity check passed"]}

def check_hazard(state: CatalystState) -> CatalystState:
    return {"history": ["Hazard classification finalized"]}

builder = StateGraph(CatalystState)
builder.add_node("purity_check", validate_purity)
builder.add_node("hazard_check", check_hazard)
builder.add_edge("purity_check", "hazard_check")
builder.add_edge("hazard_check", END)
builder.set_entry_point("purity_check")
graph = builder.compile()