from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_compliant: bool
    approved: bool

def validate_api(state: ProcurementState):
    if state['purity'] >= 99.0 and state['gmp_compliant']:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_api)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
