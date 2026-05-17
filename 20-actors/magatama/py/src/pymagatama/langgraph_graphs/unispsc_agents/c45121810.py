from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicrofilmState(TypedDict):
    part_number: str
    spec_verified: bool
    compatibility_checked: bool

def validate_part(state: MicrofilmState):
    state['spec_verified'] = state['part_number'].startswith('MFS-')
    return state

def check_compatibility(state: MicrofilmState):
    state['compatibility_checked'] = True
    return state

graph = StateGraph(MicrofilmState)
graph.add_node('validate', validate_part)
graph.add_node('compatibility', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatibility')
graph.add_edge('compatibility', END)
graph = graph.compile()