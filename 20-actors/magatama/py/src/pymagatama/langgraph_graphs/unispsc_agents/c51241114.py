from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_certified: bool
    approved: bool

def validate_chemistry(state: ProcurementState) -> dict:
    if state['purity'] >= 99.0 and state['gmp_certified']:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemistry)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()