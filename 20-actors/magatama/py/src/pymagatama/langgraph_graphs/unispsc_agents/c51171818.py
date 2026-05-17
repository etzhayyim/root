from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    storage_temp: float
    compliance_cert: str
    approved: bool

def validate_purity(state: PharmState) -> PharmState:
    state['approved'] = state['purity'] >= 99.0
    return state

def check_storage(state: PharmState) -> PharmState:
    if state['storage_temp'] > 25.0:
        state['approved'] = False
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.add_node('storage', check_storage)
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph.set_entry_point('validate')