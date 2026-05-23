from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CelecoxibState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_certified: bool
    approved: bool

def validate_quality(state: CelecoxibState) -> CelecoxibState:
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_certified']
    return state

workflow = StateGraph(CelecoxibState)
workflow.add_node('validate', validate_quality)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
