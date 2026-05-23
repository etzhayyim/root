from typing import TypedDict
from langgraph.graph import StateGraph, END

class PressState(TypedDict):
    specs: dict
    is_compliant: bool
    safety_score: float

def validate_specs(state: PressState):
    force = state['specs'].get('pressing_force_kn', 0)
    state['is_compliant'] = force > 0
    return state

def check_safety(state: PressState):
    state['safety_score'] = 1.0 if state['is_compliant'] else 0.0
    return state

graph = StateGraph(PressState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', check_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
