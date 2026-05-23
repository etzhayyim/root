from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrumHandlingState(TypedDict):
    load_capacity: float
    safety_check: bool
    is_compliant: bool

def validate_specs(state: DrumHandlingState):
    state['is_compliant'] = state['load_capacity'] > 0
    return state

def inspect_safety(state: DrumHandlingState):
    state['safety_check'] = True
    return state

graph = StateGraph(DrumHandlingState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', inspect_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
