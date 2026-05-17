from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProtectorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_impact(state: ProtectorState):
    rating = state['spec_data'].get('impact_rating', 0)
    if rating < 5: state['validation_errors'].append('Insufficient impact rating')
    return state

def check_compliance(state: ProtectorState):
    state['is_approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(ProtectorState)
graph.add_node('validate', validate_impact)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()