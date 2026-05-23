from typing import TypedDict
from langgraph.graph import StateGraph, END

class WoundAbsorberState(TypedDict):
    product_specs: dict
    compliance_verified: bool

def validate_sterility(state: WoundAbsorberState):
    state['compliance_verified'] = 'sterilization_cert' in state['product_specs']
    return state

def check_biocompatibility(state: WoundAbsorberState):
    if state.get('compliance_verified'):
        state['compliance_verified'] = 'bio_iso_code' in state['product_specs']
    return state

graph = StateGraph(WoundAbsorberState)
graph.add_node('validate', validate_sterility)
graph.add_node('bio_check', check_biocompatibility)
graph.add_edge('validate', 'bio_check')
graph.add_edge('bio_check', END)
graph.set_entry_point('validate')
