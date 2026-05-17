from typing import TypedDict
from langgraph.graph import StateGraph, END

class LithiumState(TypedDict):
    purity: float
    moisture: float
    cert_exists: bool
    is_approved: bool

def validate_purity(state: LithiumState):
    state['is_approved'] = state['purity'] >= 99.5 and state['moisture'] < 0.2
    return state

def check_compliance(state: LithiumState):
    if state['cert_exists'] and state['is_approved']:
        return 'next'
    return 'flag_review'

graph = StateGraph(LithiumState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)