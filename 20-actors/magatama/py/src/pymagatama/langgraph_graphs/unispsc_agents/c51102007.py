from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_valid: bool
    compliant: bool

def validate_quality(state: PharmState):
    state['compliant'] = state['purity'] >= 99.0 and state['gmp_valid']
    return state

workflow = StateGraph(PharmState)
workflow.add_node('validate', validate_quality)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
