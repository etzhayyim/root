from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    temp_log_verified: bool
    gmp_status: str
    approved: bool

def validate_cold_chain(state: ProcurementState):
    state['temp_log_verified'] = True
    return state

def check_compliance(state: ProcurementState):
    state['approved'] = state['temp_log_verified'] and state['gmp_status'] == 'certified'
    return state

graph = StateGraph(ProcurementState)
graph.add_node('verify_cold_chain', validate_cold_chain)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('verify_cold_chain')
graph.add_edge('verify_cold_chain', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
