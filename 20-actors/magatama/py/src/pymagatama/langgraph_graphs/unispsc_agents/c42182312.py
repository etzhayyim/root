from typing import TypedDict
from langgraph.graph import StateGraph, END

class EMGState(TypedDict):
    electrode_type: str
    iso_compliance: bool
    validation_status: str

def validate_medical_compliance(state: EMGState):
    state['validation_status'] = 'COMPLIANT' if state['iso_compliance'] else 'REJECTED'
    return state

def check_material(state: EMGState):
    if 'Ag/AgCl' in state['electrode_type']:
        state['validation_status'] = 'MATERIAL_APPROVED'
    return state

graph = StateGraph(EMGState)
graph.add_node('validate', validate_medical_compliance)
graph.add_node('material_check', check_material)
graph.add_edge('validate', 'material_check')
graph.add_edge('material_check', END)
graph.set_entry_point('validate')
graph = graph.compile()