from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClutchProcurementState(TypedDict):
    part_number: str
    material_specs: dict
    compliance_checks: List[str]
    approved: bool

def validate_specs(state: ClutchProcurementState):
    # Simulate CAD/Spec validation logic
    state['compliance_checks'].append('Dimensional accuracy verified')
    state['approved'] = True
    return state

def run_quality_assurance(state: ClutchProcurementState):
    state['compliance_checks'].append('Friction material test passed')
    return state

graph = StateGraph(ClutchProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('qa', run_quality_assurance)
graph.add_edge('validate', 'qa')
graph.add_edge('qa', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()