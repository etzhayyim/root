from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    viscosity: float
    coa_verified: bool
    approved: bool

def validate_purity(state: ChemicalState):
    state['approved'] = state['purity'] >= 99.0 and state['coa_verified']
    return state

workflow = StateGraph(ChemicalState)
workflow.add_node('qc_check', validate_purity)
workflow.set_entry_point('qc_check')
workflow.add_edge('qc_check', END)
graph = workflow.compile()