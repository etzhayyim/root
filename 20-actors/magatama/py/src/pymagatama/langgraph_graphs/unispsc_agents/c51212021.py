from typing import TypedDict
from langgraph.graph import StateGraph, END

class GinsengState(TypedDict):
    origin: str
    pesticide_results: dict
    approved: bool

def validate_pesticides(state: GinsengState):
    # Simulate chemical safety check
    is_safe = state['pesticide_results'].get('safe', False)
    return {'approved': is_safe}

def route_by_approval(state: GinsengState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(GinsengState)
graph.add_node('validate', validate_pesticides)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
