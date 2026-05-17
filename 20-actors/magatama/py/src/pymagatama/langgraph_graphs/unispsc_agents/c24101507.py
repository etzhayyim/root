from typing import TypedDict
from langgraph.graph import StateGraph, END

class WheelbarrowState(TypedDict):
    load_capacity: int
    material: str
    is_compliant: bool

def validate_load_capacity(state: WheelbarrowState):
    state['is_compliant'] = state['load_capacity'] >= 100
    return state

def route_by_compliance(state: WheelbarrowState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(WheelbarrowState)
graph.add_node('validate', validate_load_capacity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()