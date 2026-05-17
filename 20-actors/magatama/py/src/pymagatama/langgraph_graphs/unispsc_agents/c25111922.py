from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MooringSpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_load_capacity(state: MooringSpecState):
    capacity = state['spec_data'].get('load_capacity_kg', 0)
    if capacity <= 0:
        state['validation_errors'].append('Invalid load capacity')
    return state

def check_compliance(state: MooringSpecState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(MooringSpecState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()