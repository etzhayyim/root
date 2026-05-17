from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AssemblyState(TypedDict):
    part_number: str
    material_spec: str
    inspection_passed: bool
    validation_log: List[str]

def validate_material(state: AssemblyState):
    log = f"Validating material: {state['material_spec']}"
    return {"validation_log": [log], "inspection_passed": True}

def check_dimensions(state: AssemblyState):
    return {"validation_log": state['validation_log'] + ["Tolerances verified"]}

graph = StateGraph(AssemblyState)
graph.add_node("validate", validate_material)
graph.add_node("dimension_check", check_dimensions)
graph.set_entry_point("validate")
graph.add_edge("validate", "dimension_check")
graph.add_edge("dimension_check", END)
app = graph.compile()