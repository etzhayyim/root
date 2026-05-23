from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    assembly_id: str
    material_spec: dict
    validation_passed: bool

def validate_structural_integrity(state: AssemblyState):
    print(f"Validating structural integrity for {state['assembly_id']}")
    state['validation_passed'] = True
    return state

def check_compliance(state: AssemblyState):
    print("Checking material mill test report conformity")
    return state

graph = StateGraph(AssemblyState)
graph.add_node("validate", validate_structural_integrity)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
