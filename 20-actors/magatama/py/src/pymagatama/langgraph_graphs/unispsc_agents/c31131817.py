from langgraph.graph import StateGraph, END
from typing import TypedDict

class ForgeState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_geometry(state: ForgeState):
    # Simulate CAD/Dimension validation logic
    state['validation_passed'] = all(val > 0 for val in state['spec_data'].values())
    return state

def check_material_certs(state: ForgeState):
    # Verify metallurgical compliance
    has_certs = state['spec_data'].get('has_iso_cert', False)
    state['validation_passed'] = state['validation_passed'] and has_certs
    return state

graph = StateGraph(ForgeState)
graph.add_node('geometry_check', validate_geometry)
graph.add_node('cert_check', check_material_certs)
graph.set_entry_point('geometry_check')
graph.add_edge('geometry_check', 'cert_check')
graph.add_edge('cert_check', END)
graph = graph.compile()
