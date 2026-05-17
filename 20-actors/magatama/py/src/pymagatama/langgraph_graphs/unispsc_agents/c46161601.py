from typing import TypedDict
from langgraph.graph import StateGraph, END

class RopeState(TypedDict):
    material: str
    tensile_strength: float
    inspection_passed: bool

def validate_specs(state: RopeState) -> RopeState:
    if state['tensile_strength'] > 0:
        state['inspection_passed'] = True
    return state

def flag_risks(state: RopeState) -> RopeState:
    return state

graph = StateGraph(RopeState)
graph.add_node('validate', validate_specs)
graph.add_node('risk', flag_risks)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk')
graph.add_edge('risk', END)
graph = graph.compile()