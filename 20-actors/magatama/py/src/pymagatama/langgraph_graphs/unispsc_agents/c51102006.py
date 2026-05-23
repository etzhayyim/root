from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_msds: bool
    is_compliant: bool

def validate_purity(state: ChemicalState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['has_msds']
    return state

def check_safety(state: ChemicalState):
    return 'compliant' if state['is_compliant'] else 'rejected'

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_safety, {'compliant': END, 'rejected': END})
graph.compile()
