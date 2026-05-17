from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    gmp_certified: bool
    compliant: bool

def validate_pharma_specs(state: ProcurementState):
    state['compliant'] = state['purity_level'] >= 99.0 and state['gmp_certified']
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_pharma_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()