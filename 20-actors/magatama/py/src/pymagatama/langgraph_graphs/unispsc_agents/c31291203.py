from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrassComponentState(TypedDict):
    part_number: str
    material_grade: str
    tolerances: dict
    is_validated: bool

def validate_specs(state: BrassComponentState):
    print(f"Validating specs for {state['part_number']}")
    # Logic to check tolerance parameters
    return {"is_validated": True}

def prepare_production(state: BrassComponentState):
    print("Initializing extrusion sequence")
    return {"is_validated": True}

graph = StateGraph(BrassComponentState)
graph.add_node("validate", validate_specs)
graph.add_node("production", prepare_production)
graph.add_edge("validate", "production")
graph.add_edge("production", END)
graph.set_entry_point("validate")
graph = graph.compile()