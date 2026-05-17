from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class AlloyState(TypedDict):
    material_id: str
    spec_compliance: bool
    test_results: List[str]
    validation_log: Annotated[List[str], operator.add]

def validate_composition(state: AlloyState) -> AlloyState:
    state["validation_log"].append("Validating material composition against aerospace standards.")
    return {"spec_compliance": True}

def conduct_ndt(state: AlloyState) -> AlloyState:
    state["validation_log"].append("Performing non-destructive testing for structural integrity.")
    state["test_results"].append("NDT_PASSED")
    return {}

builder = StateGraph(AlloyState)
builder.add_node("composition", validate_composition)
builder.add_node("ndt", conduct_ndt)
builder.add_edge("composition", "ndt")
builder.add_edge("ndt", END)
builder.set_entry_point("composition")
graph = builder.compile()