from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_sds: bool
    is_compliant: bool

def validate_purity(state: ChemicalState):
    state['is_compliant'] = state['purity'] >= 0.95
    return state

def check_documentation(state: ChemicalState):
    if not state.get('has_sds'):
        raise ValueError('SDS required for hazardous materials')
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('docs', check_documentation)
graph.set_entry_point('validate')
graph.add_edge('validate', 'docs')
graph.add_edge('docs', END)
app = graph.compile()