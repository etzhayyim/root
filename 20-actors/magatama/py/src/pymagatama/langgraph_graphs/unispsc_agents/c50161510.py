from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SweetenerState(TypedDict):
    purity_level: float
    certifications: List[str]
    approved: bool

def validate_purity(state: SweetenerState):
    state['approved'] = state['purity_level'] >= 99.5
    return state

def check_certifications(state: SweetenerState):
    required = {'HACCP', 'ISO22000'}
    state['approved'] = state['approved'] and required.issubset(set(state['certifications']))
    return state

graph = StateGraph(SweetenerState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_certifications', check_certifications)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_certifications')
graph.add_edge('check_certifications', END)
graph = graph.compile()