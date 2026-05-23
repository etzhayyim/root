from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    compliance: bool
    approved: bool

def validate_quality(state: PharmaState):
    state['compliance'] = state['purity'] >= 99.0
    return state

def approval_check(state: PharmaState):
    state['approved'] = state['compliance']
    return state

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_quality)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
app = graph.compile()
