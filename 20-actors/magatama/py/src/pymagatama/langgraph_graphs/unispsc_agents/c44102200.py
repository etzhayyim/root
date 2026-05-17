from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScannerState(TypedDict):
    part_number: str
    compatibility_verified: bool
    order_approved: bool

def validate_part(state: ScannerState):
    # Simulate part validation logic
    state['compatibility_verified'] = state['part_number'].startswith('SCAN-')
    return state

def check_approval(state: ScannerState):
    state['order_approved'] = state['compatibility_verified']
    return state

graph = StateGraph(ScannerState)
graph.add_node('validate', validate_part)
graph.add_node('approval', check_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()