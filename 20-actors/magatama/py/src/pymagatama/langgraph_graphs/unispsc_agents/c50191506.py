from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoupProcurementState(TypedDict):
    supply_chain_temp: float
    inspection_passed: bool
    is_compliant: bool

def validate_cold_chain(state: SoupProcurementState):
    state['is_compliant'] = state['supply_chain_temp'] <= -18.0
    return state

def check_quality(state: SoupProcurementState):
    state['inspection_passed'] = state['is_compliant']
    return state

graph = StateGraph(SoupProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('inspect', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
