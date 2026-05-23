from typing import TypedDict
from langgraph.graph import StateGraph, END

class CaulkState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_compliance(state: CaulkState):
    # Business logic for VOC compliance check
    voc_limit = 50.0
    state['is_compliant'] = state['spec_data'].get('voc_emission_rating', 100) <= voc_limit
    return state

def check_storage(state: CaulkState):
    # Logic for storage temp validation
    if 'storage_temperature_conditions' not in state['spec_data']:
        state['is_compliant'] = False
    return state

graph = StateGraph(CaulkState)
graph.add_node('validate', validate_compliance)
graph.add_node('storage_check', check_storage)
graph.add_edge('validate', 'storage_check')
graph.add_edge('storage_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
