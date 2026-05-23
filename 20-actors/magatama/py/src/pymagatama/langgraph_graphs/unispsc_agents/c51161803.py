from typing import TypedDict
from langgraph.graph import StateGraph, END

class MentholState(TypedDict):
    purity: float
    coas_received: bool
    compliant: bool

def validate_purity(state: MentholState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_docs(state: MentholState):
    state['compliant'] = state['compliant'] and state['coas_received']
    return state

graph = StateGraph(MentholState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_docs', check_docs)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_docs')
graph.add_edge('check_docs', END)
graph = graph.compile()
