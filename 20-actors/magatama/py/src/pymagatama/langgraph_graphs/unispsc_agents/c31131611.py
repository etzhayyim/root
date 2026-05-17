from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_id: str
    material_spec: str
    tolerance: float
    qc_passed: bool

def validate_material(state: ForgingState):
    print(f"Validating material spec for {state['part_id']}...")
    return {"qc_passed": state['material_spec'] == 'C3604'}

def check_dimensions(state: ForgingState):
    print(f"Checking tolerancing for {state['part_id']}...")
    return {"qc_passed": state['tolerance'] < 0.05}

graph = StateGraph(ForgingState)
graph.add_node("validate", validate_material)
graph.add_node("dimensions", check_dimensions)
graph.set_entry_point("validate")
graph.add_edge("validate", "dimensions")
graph.add_edge("dimensions", END)
app = graph.compile()