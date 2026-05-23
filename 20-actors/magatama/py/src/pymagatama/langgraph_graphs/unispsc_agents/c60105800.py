from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_type: str
    curriculum_level: str
    is_compliant: bool

def validate_material(state: ProcurementState):
    print(f'Validating material: {state["material_type"]}')
    return {"is_compliant": True}

def check_curriculum(state: ProcurementState):
    print(f'Checking alignment for {state["curriculum_level"]}')
    return {"is_compliant": True}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_material)
graph.add_node("curriculum", check_curriculum)
graph.set_entry_point("validate")
graph.add_edge("validate", "curriculum")
graph.add_edge("curriculum", END)
app = graph.compile()
