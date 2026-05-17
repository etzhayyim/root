from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FinasterideState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_verified: bool
    approved: bool

def validate_compliance(state: FinasterideState):
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_verified']
    return state

workflow = StateGraph(FinasterideState)
workflow.add_node('validate', validate_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()