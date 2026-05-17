from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrganizerState(TypedDict):
    item_name: str
    specs: dict
    is_verified: bool

def validate_specs(state: OrganizerState):
    required = ['Material', 'Dimensions']
    state['is_verified'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: OrganizerState):
    print(f'Checking compliance for {state['item_name']}')
    return state

graph = StateGraph(OrganizerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()