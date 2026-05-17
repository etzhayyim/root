from typing import TypedDict
from langgraph.graph import StateGraph, END

class TinProcurementState(TypedDict):
    purity_level: float
    dimensions: str
    compliance_checked: bool

def validate_purity(state: TinProcurementState):
    state['compliance_checked'] = state['purity_level'] >= 99.9
    return state

workflow = StateGraph(TinProcurementState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()