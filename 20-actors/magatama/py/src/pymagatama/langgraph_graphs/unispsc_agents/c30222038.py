from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TunnelState(TypedDict):
    project_id: str
    specs: dict
    validation_passed: bool
    approvals: List[str]

def validate_structural_specs(state: TunnelState):
    # Simulate CAD/Structural validation logic
    state['validation_passed'] = 'Structural Design Code' in state['specs']
    return state

def check_compliance(state: TunnelState):
    # Simulate regulatory compliance checks
    state['approvals'] = ['Geotechnical', 'Safety'] if state['validation_passed'] else []
    return state

graph = StateGraph(TunnelState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
