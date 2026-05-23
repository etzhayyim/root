from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    quality_docs: dict
    approved: bool

def validate_gmp(state: ProcurementState):
    state['approved'] = state['quality_docs'].get('gmp_verified', False)
    return state

def check_temp_logs(state: ProcurementState):
    # Simulate temperature validation logic
    temp_stable = state['quality_docs'].get('temp_log_status') == 'pass'
    state['approved'] = state['approved'] and temp_stable
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_temp_logs', check_temp_logs)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_temp_logs')
graph.add_edge('check_temp_logs', END)
graph = graph.compile()
