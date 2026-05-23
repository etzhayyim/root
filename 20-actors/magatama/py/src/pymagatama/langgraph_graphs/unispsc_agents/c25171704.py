from typing import TypedDict
from langgraph.graph import StateGraph, END

class DragChuteState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: DragChuteState):
    # Business logic for aerospace drag chute verification
    has_certs = 'AS9100' in state['spec_data'].get('certs', [])
    return {'validated': has_certs}

def perform_safety_check(state: DragChuteState):
    # Dual-use export control screening
    is_safe = state['spec_data'].get('export_licensed', False)
    return {'compliance_check': is_safe}

graph = StateGraph(DragChuteState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', perform_safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
