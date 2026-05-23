from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class PipeState(TypedDict):
    material_spec: str
    weld_quality_check: bool
    pressure_test_passed: bool
    is_compliant: bool
def validate_material(state: PipeState):
    return {"is_compliant": state["material_spec"] == "Al-6061-T6"}
def check_quality(state: PipeState):
    return {"is_compliant": state["weld_quality_check"] and state["pressure_test_passed"]}
graph = StateGraph(PipeState)
graph.add_node("validate_material", validate_material)
graph.add_node("check_quality", check_quality)
graph.add_edge("validate_material", "check_quality")
graph.add_edge("check_quality", END)
graph.set_entry_point("validate_material")
graph = graph.compile()
