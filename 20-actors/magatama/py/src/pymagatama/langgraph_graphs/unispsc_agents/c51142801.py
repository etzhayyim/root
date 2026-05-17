from typing import TypedDict
from langgraph.graph import StateGraph, END

class RiluzoleState(TypedDict):
    purity: float
    gmp_status: bool
    approved: bool

def validate_purity(state: RiluzoleState):
    return {'approved': state['purity'] >= 99.0 and state['gmp_status']}

graph = StateGraph(RiluzoleState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()