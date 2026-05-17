from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_spec: dict
    validation_results: dict
    approved: bool

def validate_material(state: ProcurementState):
    # Simulate CAD and material spec compliance check
    alloy = state['material_spec'].get('alloy')
    state['validation_results'] = {'alloy_check': alloy == '6061-T6', 'ndt_check': True}
    state['approved'] = state['validation_results']['alloy_check']
    return state

def verify_bonding(state: ProcurementState):
    # Simulate bonding process verification
    state['validation_results']['bonding_verified'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('verify', verify_bonding)
graph.add_edge('validate', 'verify')
graph.add_edge('verify', END)
graph.set_entry_point('validate')
graph = graph.compile()