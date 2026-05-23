from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec: dict
    validation_results: Annotated[list[str], operator.add]
    is_approved: bool

def validate_load_capacity(state: BearingState):
    res = "Load capacity meets industrial standards." if state["spec"].get("load") > 1000 else "Load capacity insufficient."
    return {"validation_results": [res], "is_approved": res.startswith("Load")}

def check_material_specs(state: BearingState):
    res = "Material specs verified." if state["spec"].get("material") == "high_carbon_steel" else "Invalid material."
    return {"validation_results": [res]}

builder = StateGraph(BearingState)
builder.add_node("validate_load", validate_load_capacity)
builder.add_node("check_material", check_material_specs)
builder.add_edge("validate_load", "check_material")
builder.add_edge("check_material", END)
builder.set_entry_point("validate_load")
graph = builder.compile()
