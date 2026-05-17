from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    material_id: str
    purity_level: float
    gmp_verified: bool
    approved: bool

def validate_quality(state: PharmaState) -> PharmaState:
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_verified']
    return state

workflow = StateGraph(PharmaState)
workflow.add_node('validate', validate_quality)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()