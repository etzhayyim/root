from typing import TypedDict
from langgraph.graph import StateGraph, END

class InspectionState(TypedDict):
    resolution: int
    ip_rating: str
    inspection_passed: bool

def validate_specs(state: InspectionState):
    state['inspection_passed'] = state['resolution'] >= 1080 and state['ip_rating'] == 'IP68'
    return state

graph = StateGraph(InspectionState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()