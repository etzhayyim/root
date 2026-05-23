from typing import TypedDict
from langgraph.graph import StateGraph, END

class ArnicaState(TypedDict):
    purity: float
    contaminants: dict
    is_compliant: bool

def validate_purity(state: ArnicaState):
    state['is_compliant'] = state['purity'] >= 98.0
    return state

def check_compliance(state: ArnicaState):
    return 'compliant' if state['is_compliant'] else 'rejected'

workflow = StateGraph(ArnicaState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', check_compliance, {'compliant': END, 'rejected': END})
graph = workflow.compile()
