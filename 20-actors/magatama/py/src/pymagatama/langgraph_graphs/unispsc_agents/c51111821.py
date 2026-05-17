from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PharmaState(TypedDict):
    material_id: str
    purity_level: float
    has_coa: bool
    is_compliant: bool

def validate_purity(state: PharmaState):
    state['is_compliant'] = state['purity_level'] >= 99.0 and state['has_coa']
    return state

workflow = StateGraph(PharmaState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()