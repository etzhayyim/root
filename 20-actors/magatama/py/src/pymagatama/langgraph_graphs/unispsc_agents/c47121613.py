from typing import TypedDict
from langgraph.graph import StateGraph, END

class PolisherState(TypedDict):
    part_number: str
    compatibility_verified: bool
    inspection_passed: bool

def check_compatibility(state: PolisherState):
    state['compatibility_verified'] = state['part_number'].startswith('ACC-')
    return 'verified_node'

def run_inspection(state: PolisherState):
    state['inspection_passed'] = state['compatibility_verified']
    return 'end_node'

graph = StateGraph(PolisherState)
graph.add_node('verify', check_compatibility)
graph.add_node('inspect', run_inspection)
graph.set_entry_point('verify')
graph.add_edge('verify', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
