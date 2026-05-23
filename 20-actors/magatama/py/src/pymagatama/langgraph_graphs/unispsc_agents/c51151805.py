from typing import TypedDict
from langgraph.graph import StateGraph, END

class TimololState(TypedDict):
    purity: float
    gmp_certified: bool
    compliant: bool

def validate_purity(state: TimololState):
    state['compliant'] = state['purity'] >= 99.0 and state['gmp_certified']
    return state

def route_by_compliance(state: TimololState):
    return 'process' if state['compliant'] else 'reject'

graph = StateGraph(TimololState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END, 'reject': END})
