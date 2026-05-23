from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specs: dict
    validation_status: bool

def validate_casting_specs(state: CastingState):
    required = ['material', 'tolerance', 'surface_finish']
    state['validation_status'] = all(k in state['specs'] for k in required)
    return state

def route_procurement(state: CastingState):
    return 'approve' if state['validation_status'] else 'reject'

graph = StateGraph(CastingState)
graph.add_node('validate', validate_casting_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
