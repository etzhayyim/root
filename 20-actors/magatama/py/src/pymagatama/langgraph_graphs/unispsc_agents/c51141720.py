from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_verified: bool
    compliant: bool

def validate_purity(state: PharmState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_compliance(state: PharmState):
    return 'compliant' if state['gmp_verified'] and state['compliant'] else 'non_compliant'

workflow = StateGraph(PharmState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph = workflow.compile()