from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LeadProcureState(TypedDict):
    purity: float
    dimensions: str
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: LeadProcureState):
    state['approved'] = state['purity'] >= 99.9
    return state

def check_dimensions(state: LeadProcureState):
    if not state.get('dimensions'):
        state['approved'] = False
    return state

graph = StateGraph(LeadProcureState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_dimensions', check_dimensions)
graph.add_edge('validate_purity', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()
