from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CimetidineState(TypedDict):
    purity: float
    meets_pharmacopoeia: bool
    compliant: bool

def validate_purity(state: CimetidineState):
    print('Validating Purity...')
    state['compliant'] = state['purity'] >= 99.0 and state['meets_pharmacopoeia']
    return state

def approval_check(state: CimetidineState):
    return 'compliant' if state['compliant'] else 'rejected'

graph = StateGraph(CimetidineState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)