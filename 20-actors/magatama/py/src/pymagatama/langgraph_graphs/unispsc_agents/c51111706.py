from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    compliance_cleared: bool
    safety_check_passed: bool

def validate_pharma_compliance(state: ProcurementState):
    print(f'Validating GMP certification for {state[\'material_name\']}')
    return {\'compliance_cleared\': True}

def safety_protocol_verification(state: ProcurementState):
    print(\'Running hazardous material safety verification...\')
    return {\'safety_check_passed\': True}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_pharma_compliance)
graph.add_node("safety", safety_protocol_verification)
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("validate")
graph = graph.compile()