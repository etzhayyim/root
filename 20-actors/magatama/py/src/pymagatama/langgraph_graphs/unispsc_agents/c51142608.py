from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    compliant: bool
    approved: bool

def validate_purity(state: ChemicalState):
    state['compliant'] = state.get('purity', 0) >= 99.0
    return 'process_approval'

def process_approval(state: ChemicalState):
    state['approved'] = state['compliant']
    return 'end'

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('process_approval', process_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process_approval')
graph.add_edge('process_approval', END)
graph = graph.compile()
