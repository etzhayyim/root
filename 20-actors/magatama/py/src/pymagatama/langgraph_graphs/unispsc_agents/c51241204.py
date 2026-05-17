from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_sds: bool
    is_compliant: bool

def validate_purity(state: ChemicalState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['has_sds']
    return state

def check_compliance(state: ChemicalState):
    return 'compliant' if state['is_compliant'] else 'rejected'

workflow = StateGraph(ChemicalState)
workflow.add_node('validator', validate_purity)
workflow.add_edge('validator', END)
workflow.set_entry_point('validator')
graph = workflow.compile()