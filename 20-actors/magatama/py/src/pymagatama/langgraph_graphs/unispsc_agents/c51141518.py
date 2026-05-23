from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_verified: bool
    compliant: bool

def validate_purity(state: PharmState):
    state['compliant'] = state['purity'] >= 99.9
    return state

def check_compliance(state: PharmState):
    return 'compliant' if state['gmp_verified'] and state['compliant'] else 'reject'

workflow = StateGraph(PharmState)
workflow.add_node('validate', validate_purity)
workflow.add_edge('validate', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
