from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrassAssemblyState(TypedDict):
    spec: dict
    validation_passed: bool

def validate_materials(state: BrassAssemblyState):
    # Perform check on chemical composition compatibility
    state['validation_passed'] = 'brass_grade' in state['spec']
    return state

def check_welding_standards(state: BrassAssemblyState):
    # Simulate ISO or ASTM welding standard inspection
    return {"validation_passed": True}

graph = StateGraph(BrassAssemblyState)
graph.add_node("material_check", validate_materials)
graph.add_node("welding_audit", check_welding_standards)
graph.add_edge("material_check", "welding_audit")
graph.add_edge("welding_audit", END)
graph.set_entry_point("material_check")
graph = graph.compile()
