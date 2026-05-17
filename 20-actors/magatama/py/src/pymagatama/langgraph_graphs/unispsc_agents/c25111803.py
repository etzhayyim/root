from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoatState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_buoyancy(state: BoatState):
    capacity = state['spec_data'].get('capacity', 0)
    state['is_compliant'] = capacity > 0
    return state

def safety_check(state: BoatState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(BoatState)
graph.add_node('validate', validate_buoyancy)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()