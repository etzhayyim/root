from typing import TypedDict
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    specs: dict
    validation_score: float
    is_compliant: bool

def validate_specs(state: DispenserState):
    # Simulate CAD/Spec validation logic for bulk dispensers
    state['is_compliant'] = state['specs'].get('flow_rate') > 0
    state['validation_score'] = 1.0 if state['is_compliant'] else 0.0
    return state

def check_safety(state: DispenserState):
    # Industry specific compliance check
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(DispenserState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', check_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
