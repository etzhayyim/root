from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CleaningProductState(TypedDict):
    product_name: str
    sds_verified: bool
    hazard_class: str
    inspection_passed: bool

def check_sds(state: CleaningProductState):
    return {"sds_verified": True}

def validate_hazardous_materials(state: CleaningProductState):
    return {"inspection_passed": True if state['hazard_class'] != "Explosive" else False}

graph = StateGraph(CleaningProductState)
graph.add_node("check_sds", check_sds)
graph.add_node("validate_hazmat", validate_hazardous_materials)
graph.set_entry_point("check_sds")
graph.add_edge("check_sds", "validate_hazmat")
graph.add_edge("validate_hazmat", END)
compiled_graph = graph.compile()
