from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: bool
    approved: bool

def validate_chemical(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0 and state['compliance_docs'] is True
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_chemical)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()