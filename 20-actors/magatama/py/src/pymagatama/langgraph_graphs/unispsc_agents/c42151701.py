from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalChairState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_ergonomics(state: DentalChairState):
    state['is_compliant'] = state['spec_data'].get('adjustability_degree', 0) > 0
    return state

def check_certification(state: DentalChairState):
    state['is_compliant'] = state['is_compliant'] and 'ISO13485' in state['spec_data'].get('certs', [])
    return state

graph = StateGraph(DentalChairState)
graph.add_node('validate', validate_ergonomics)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
app = graph.compile()