from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: PharmaState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_docs(state: PharmaState):
    state['approved'] = state['approved'] and 'CoA' in state['compliance_docs']
    return state

graph = StateGraph(PharmaState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_docs', check_docs)
graph.add_edge('validate_purity', 'check_docs')
graph.add_edge('check_docs', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()