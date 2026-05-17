from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TelephonePartState(TypedDict):
    part_id: str
    spec_check: bool
    compatibility_verified: bool

def validate_part(state: TelephonePartState):
    state['spec_check'] = True
    return 'check_compatibility'

def check_compatibility(state: TelephonePartState):
    state['compatibility_verified'] = True
    return END

graph = StateGraph(TelephonePartState)
graph.add_node('validate', validate_part)
graph.add_node('check_compatibility', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_compatibility')
graph.add_edge('check_compatibility', END)
graph = graph.compile()