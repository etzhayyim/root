from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForkliftSpecState(TypedDict):
    capacity: float
    safety_compliant: bool
    engine_type: str

def validate_specs(state: ForkliftSpecState):
    state['safety_compliant'] = state['capacity'] > 0
    return state

def check_compliance(state: ForkliftSpecState):
    return 'valid' if state['safety_compliant'] else 'invalid'

graph = StateGraph(ForkliftSpecState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
