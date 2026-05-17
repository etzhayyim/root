from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity_level: float
    has_coa: bool
    compliant: bool

def validate_quality(state: PharmState) -> PharmState:
    state['compliant'] = state['purity_level'] >= 99.5 and state['has_coa']
    return state

workflow = StateGraph(PharmState)
workflow.add_node('validate_quality', validate_quality)
workflow.set_entry_point('validate_quality')
workflow.add_edge('validate_quality', END)

graph = workflow.compile()