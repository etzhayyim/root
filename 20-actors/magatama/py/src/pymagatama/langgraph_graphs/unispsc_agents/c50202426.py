from langgraph.graph import StateGraph, END
from typing import TypedDict

class TangeloState(TypedDict):
    brix: float
    safety_cleared: bool
    approved: bool

def validate_quality(state: TangeloState):
    state['safety_cleared'] = (state['brix'] >= 50.0)
    return state

def check_compliance(state: TangeloState):
    state['approved'] = state['safety_cleared']
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(TangeloState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()