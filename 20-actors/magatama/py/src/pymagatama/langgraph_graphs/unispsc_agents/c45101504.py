from typing import TypedDict
from langgraph.graph import StateGraph, END

class LithographyState(TypedDict):
    spec_sheet: dict
    compliance_check: bool
    export_license_verified: bool

def validate_specs(state: LithographyState) -> LithographyState:
    required = ['resolution', 'wavelength']
    state['compliance_check'] = all(k in state['spec_sheet'] for k in required)
    return state

def check_export(state: LithographyState) -> LithographyState:
    state['export_license_verified'] = True
    return state

graph = StateGraph(LithographyState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()
