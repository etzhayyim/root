from langgraph.graph import StateGraph, END
from typing import TypedDict
class PharmaState(TypedDict):
    purity: float
    has_gmp_cert: bool
    is_compliant: bool
def validate_purity(state: PharmaState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['has_gmp_cert']
    return state
graph = StateGraph(PharmaState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
