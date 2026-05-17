from typing import TypedDict
from langgraph.graph import StateGraph, END
class ChemicalState(TypedDict):
    purity: float
    has_msds: bool
    is_approved: bool
def validate_purity(state: ChemicalState):
    state['is_approved'] = state['purity'] >= 99.0
    return 'approved' if state['is_approved'] else 'rejected'
def process_order(state: ChemicalState):
    return state
graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()