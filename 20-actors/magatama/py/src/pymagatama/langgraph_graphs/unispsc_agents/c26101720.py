from typing import TypedDict
from langgraph.graph import StateGraph, END

class TurboState(TypedDict):
    part_id: str
    inspection_passed: bool
    thermal_rating: float

def validate_specs(state: TurboState):
    state['inspection_passed'] = state['thermal_rating'] > 800.0
    return state

def route_verification(state: TurboState):
    return 'pass' if state['inspection_passed'] else 'fail'

graph = StateGraph(TurboState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
