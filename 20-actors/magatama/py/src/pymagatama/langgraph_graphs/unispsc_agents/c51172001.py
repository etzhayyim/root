from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChenodiolState(TypedDict):
    purity: float
    compliance_docs: bool
    approved: bool

def validate_purity(state: ChenodiolState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_docs(state: ChenodiolState):
    return state

graph = StateGraph(ChenodiolState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_docs', check_docs)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_docs')
graph.add_edge('check_docs', END)
graph.compile()