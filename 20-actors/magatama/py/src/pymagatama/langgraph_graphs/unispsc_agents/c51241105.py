from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    storage_temp: float
    is_gmp_certified: bool
    approved: bool

def validate_specifications(state: ProcurementState):
    state['approved'] = (state['purity'] >= 99.0 and state['storage_temp'] <= 5.0 and state['is_gmp_certified'])
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specifications)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
