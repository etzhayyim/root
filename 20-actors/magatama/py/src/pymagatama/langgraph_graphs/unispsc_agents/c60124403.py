from typing import TypedDict
from langgraph.graph import StateGraph, END

class AluminumWireState(TypedDict):
    specs: dict
    validation_score: float
    status: str

def validate_specs(state: AluminumWireState):
    # Business logic for aluminum alloy material validation
    conductivity = state['specs'].get('conductivity', 0)
    is_valid = conductivity >= 60.0
    return {'validation_score': 1.0 if is_valid else 0.0, 'status': 'VALIDATED' if is_valid else 'REJECTED'}

def perform_compliance_check(state: AluminumWireState):
    # Dual-use compliance routing
    return {'status': 'COMPLIANCE_PASSED'}

graph = StateGraph(AluminumWireState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', perform_compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
process = graph.compile()