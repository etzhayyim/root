from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    dimensions: dict
    purity_level: float
    inspection_passed: bool

def validate_specs(state: ForgingState) -> ForgingState:
    state['inspection_passed'] = state['purity_level'] >= 99.9
    return state

def shield_check(state: ForgingState) -> ForgingState:
    if state['inspection_passed']:
        print('Verification of radiation shielding density complete.')
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('shield', shield_check)
graph.add_edge('validate', 'shield')
graph.add_edge('shield', END)
graph.set_entry_point('validate')
graph = graph.compile()