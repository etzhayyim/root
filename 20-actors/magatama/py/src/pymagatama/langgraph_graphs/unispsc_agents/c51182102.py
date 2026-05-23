from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    temp_log: list[float]
    is_compliant: bool

def validate_cold_chain(state: PharmState) -> PharmState:
    state['is_compliant'] = all(2.0 <= t <= 8.0 for t in state['temp_log'])
    return state

def check_compliance(state: PharmState) -> str:
    return 'APPROVED' if state['is_compliant'] else 'REJECTED'

graph = StateGraph(PharmState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'APPROVED': END, 'REJECTED': END})
compiled = graph.compile()
