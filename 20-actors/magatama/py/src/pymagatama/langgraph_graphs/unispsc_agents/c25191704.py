from typing import TypedDict
from langgraph.graph import StateGraph, END

class StandSpecState(TypedDict):
    load_capacity: float
    safety_check: bool
    is_compliant: bool

def validate_specs(state: StandSpecState):
    state['is_compliant'] = state['load_capacity'] >= 500
    return {'is_compliant': state['is_compliant']}

def perform_safety_review(state: StandSpecState):
    state['safety_check'] = True
    return {'safety_check': True}

graph = StateGraph(StandSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', perform_safety_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()