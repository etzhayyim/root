from typing import TypedDict
from langgraph.graph import StateGraph, END

class FixativeState(TypedDict):
    chemical_name: str
    purity: float
    has_sds: bool
    is_approved: bool

def validate_chemistry(state: FixativeState) -> FixativeState:
    state['is_approved'] = state['purity'] >= 99.0 and state['has_sds']
    return state

def check_hazmat(state: FixativeState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(FixativeState)
graph.add_node('validate', validate_chemistry)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_hazmat, {'approved': END, 'rejected': END})
graph.compile()
