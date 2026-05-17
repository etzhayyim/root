from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    temperature_logs: list
    gmp_status: bool
    is_cleared: bool

def validate_cold_chain(state: ProcurementState):
    # Business logic for confirming temperature logs for biologics
    state['is_cleared'] = all(temp < 8.0 for temp in state['temperature_logs'])
    return state

def check_compliance(state: ProcurementState):
    # Verify GMP status for pharmaceutical procurement
    if state['gmp_status'] and state['is_cleared']:
        state['is_cleared'] = True
    else:
        state['is_cleared'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_temperature', validate_cold_chain)
graph.add_node('verify_gmp', check_compliance)
graph.set_entry_point('validate_temperature')
graph.add_edge('validate_temperature', 'verify_gmp')
graph.add_edge('verify_gmp', END)
graph = graph.compile()