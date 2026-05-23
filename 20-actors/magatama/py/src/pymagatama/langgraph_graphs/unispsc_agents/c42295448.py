from typing import TypedDict
from langgraph.graph import StateGraph, END

class GuardState(TypedDict):
    compliance_passed: bool
    sterility_verified: bool
    item_data: dict

def validate_sterility(state: GuardState):
    state['sterility_verified'] = state['item_data'].get('sterility_cert') is not None
    return 'check_compliance'

def check_compliance(state: GuardState):
    state['compliance_passed'] = state['sterility_verified'] and state['item_data'].get('iso_standard')
    return END

graph = StateGraph(GuardState)
graph.add_node('validate_sterility', validate_sterility)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_sterility')
graph.add_edge('validate_sterility', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
