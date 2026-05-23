from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_msds: bool
    is_approved: bool

def validate_purity(state: ChemicalState):
    state['is_approved'] = state['purity'] >= 0.99
    return state

def check_compliance(state: ChemicalState):
    if not state.get('has_msds', False):
        state['is_approved'] = False
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
