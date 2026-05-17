from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrickState(TypedDict):
    quantity: int
    spec_compliance: bool
    inspection_status: str

def validate_bricks(state: BrickState):
    state['spec_compliance'] = state['quantity'] > 0
    return state

def perform_inspection(state: BrickState):
    state['inspection_status'] = 'Quality Checked' if state['spec_compliance'] else 'Failed'
    return state

graph = StateGraph(BrickState)
graph.add_node('validate', validate_bricks)
graph.add_node('inspect', perform_inspection)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()