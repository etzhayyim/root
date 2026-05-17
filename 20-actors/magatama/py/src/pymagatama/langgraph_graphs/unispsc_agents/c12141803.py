from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MolybdenumState(TypedDict):
    purity: float
    impurities: List[str]
    approved: bool

def validate_purity(state: MolybdenumState):
    state['approved'] = state['purity'] >= 99.95
    return state

def check_impurities(state: MolybdenumState):
    if any(imp in state['impurities'] for imp in ['lead', 'arsenic']):
        state['approved'] = False
    return state

graph = StateGraph(MolybdenumState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_impurities', check_impurities)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_impurities')
graph.add_edge('check_impurities', END)
graph = graph.compile()