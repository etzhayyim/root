from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpindleState(TypedDict):
    capacity: int
    material: str
    is_compliant: bool

def validate_spindle_specs(state: SpindleState):
    state['is_compliant'] = state['capacity'] > 0 and state['material'] != 'none'
    return state

graph = StateGraph(SpindleState)
graph.add_node('validate', validate_spindle_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()