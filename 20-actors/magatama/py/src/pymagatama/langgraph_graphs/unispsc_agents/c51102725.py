from typing import TypedDict
from langgraph.graph import StateGraph, END

class HexylresorcinolState(TypedDict):
    purity: float
    cas: str
    compliant: bool

def validate_purity(state: HexylresorcinolState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_cas(state: HexylresorcinolState):
    if state['cas'] != '136-77-6':
        state['compliant'] = False
    return state

graph = StateGraph(HexylresorcinolState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cas', check_cas)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_cas')
graph.add_edge('check_cas', END)
compile_graph = graph.compile()
