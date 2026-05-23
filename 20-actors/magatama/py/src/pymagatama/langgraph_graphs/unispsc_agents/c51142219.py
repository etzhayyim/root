from langgraph.graph import StateGraph, END
from typing import TypedDict
class FentanylState(TypedDict):
    purity: float
    permit_valid: bool
    approved: bool
def validate_purity(state: FentanylState):
    state['approved'] = state['purity'] >= 99.9
    return state
def check_license(state: FentanylState):
    # Simulate regulatory check
    return state
graph = StateGraph(FentanylState)
graph.add_node('validate', validate_purity)
graph.add_node('license', check_license)
graph.set_entry_point('license')
graph.add_edge('license', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()
