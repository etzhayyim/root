from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BerylliumProcurementState(TypedDict):
    material_specs: dict
    compliance_cleared: bool
    inspection_result: str

def validate_tech_specs(state: BerylliumProcurementState):
    # Simulate CAD/Spec validation for high-precision beryllium rings
    state['compliance_cleared'] = state['material_specs'].get('purity', 0) > 99.0
    return state

def perform_quality_check(state: BerylliumProcurementState):
    state['inspection_result'] = 'Passed' if state['compliance_cleared'] else 'Failed'
    return state

graph = StateGraph(BerylliumProcurementState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('inspect', perform_quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()