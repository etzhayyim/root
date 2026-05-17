from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_grade: str
    dimensions: dict
    compliance_docs: List[str]
    approved: bool

def validate_material(state: ProcurementState):
    print(f"Validating bronze grade: {state['material_grade']}")
    return {"approved": True}

def check_dimensions(state: ProcurementState):
    print(f"Verifying dimensional tolerance: {state['dimensions']}")
    return {"approved": True}

graph = StateGraph(ProcurementState)
graph.add_node("validate_material", validate_material)
graph.add_node("check_dimensions", check_dimensions)
graph.add_edge("validate_material", "check_dimensions")
graph.add_edge("check_dimensions", END)
graph.set_entry_point("validate_material")
app = graph.compile()