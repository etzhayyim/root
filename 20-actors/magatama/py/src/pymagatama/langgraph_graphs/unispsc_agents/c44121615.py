from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StaplerState(TypedDict):
    model_number: str
    capacity: int
    is_compliant: bool

def validate_capacity(state: StaplerState):
    state['is_compliant'] = state['capacity'] >= 20
    return state

def route_procurement(state: StaplerState):
    return 'APPROVED' if state['is_compliant'] else 'REJECTED'

graph = StateGraph(StaplerState)
graph.add_node('validate', validate_capacity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
