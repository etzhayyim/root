from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    certification: str
    approved: bool

def validate_quality(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0 and 'GMP' in state['certification']
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_quality)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
