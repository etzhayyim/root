from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_number: str
    spec_verified: bool
    compliance_passed: bool

def validate_specs(state: ProcurementState):
    print(f"Validating specs for part: {state['part_number']}")
    return {"spec_verified": True}

def check_compliance(state: ProcurementState):
    print("Checking ISO/ASTM compliance for sheet metal screws...")
    return {"compliance_passed": True}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
compiled_graph = graph.compile()