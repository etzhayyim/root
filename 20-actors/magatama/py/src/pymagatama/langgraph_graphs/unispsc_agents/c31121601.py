from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    material_specs: str
    cad_file_path: str
    is_validated: bool

def validate_cad(state: CastingState):
    # Simulate CAD file depth and tolerance analysis
    return {"is_validated": True}

def check_material_compliance(state: CastingState):
    compliance = True if "ASTM" in state['material_specs'] else False
    return {"is_validated": compliance}

graph = StateGraph(CastingState)
graph.add_node("validate_cad", validate_cad)
graph.add_node("check_material", check_material_compliance)
graph.set_entry_point("validate_cad")
graph.add_edge("validate_cad", "check_material")
graph.add_edge("check_material", END)
graph = graph.compile()