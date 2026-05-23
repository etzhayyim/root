from typing import TypedDict
from langgraph.graph import StateGraph, END

class BetaineState(TypedDict):
    purity: float
    compliant: bool
    approved: bool

def validate_purity(state: BetaineState) -> dict:
    is_pure = state['purity'] >= 98.0
    return {'compliant': is_pure}

def approval_check(state: BetaineState) -> dict:
    return {'approved': state['compliant']}

graph = StateGraph(BetaineState)
graph.add_node('validate', validate_purity)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
