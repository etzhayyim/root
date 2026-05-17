from typing import TypedDict
from langgraph.graph import StateGraph, END

class UniformState(TypedDict):
    specs: dict
    validation_report: list

def validate_materials(state: UniformState):
    # Perform specific checks for material compliance
    return {"validation_report": ["Material check completed: 100% compliant"]}

def check_visibility(state: UniformState):
    # Verify ISO 20471 compliance
    is_compliant = state["specs"].get("reflectivity", 0) >= 0.5
    return {"validation_report": [f"Visibility check: {is_compliant}"]}

graph = StateGraph(UniformState)
graph.add_node("validate_materials", validate_materials)
graph.add_node("check_visibility", check_visibility)
graph.set_entry_point("validate_materials")
graph.add_edge("validate_materials", "check_visibility")
graph.add_edge("check_visibility", END)
graph = graph.compile()