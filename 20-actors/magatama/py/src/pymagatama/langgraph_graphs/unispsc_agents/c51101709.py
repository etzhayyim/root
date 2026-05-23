from typing import TypedDict
from langgraph.graph import StateGraph, END

class NiclosamideState(TypedDict):
    purity: float
    has_coa: bool
    compliant: bool

def validate_purity(state: NiclosamideState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def verify_documentation(state: NiclosamideState):
    if not state.get('has_coa', False):
        state['compliant'] = False
    return state

graph = StateGraph(NiclosamideState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_docs', verify_documentation)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'verify_docs')
graph.add_edge('verify_docs', END)
graph = graph.compile()
