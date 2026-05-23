from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_purity: float
    storage_temp: float
    is_compliant: bool

def validate_cold_chain(state: ProcurementState):
    state['is_compliant'] = state['storage_temp'] <= -20.0
    if not state['is_compliant']:
        print('Cold chain violation: Invalid temperature.')
    return state

def validate_purity(state: ProcurementState):
    if state['api_purity'] < 99.9:
        state['is_compliant'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_temp', validate_cold_chain)
graph.add_node('validate_purity', validate_purity)
graph.set_entry_point('validate_temp')
graph.add_edge('validate_temp', 'validate_purity')
graph.add_edge('validate_purity', END)
graph = graph.compile()
