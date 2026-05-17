from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_check: bool

def validate_purity(state: DrugState):
    state['compliance_check'] = state['purity'] >= 99.0 and state['gmp_certified']
    return state

graph = StateGraph(DrugState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()