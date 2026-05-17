from typing import TypedDict
from langgraph.graph import StateGraph, END

class CashBoxState(TypedDict):
    box_id: str
    lock_type: str
    is_secure: bool
    validation_log: list

def validate_lock(state: CashBoxState) -> CashBoxState:
    secure_types = ['keyed', 'electronic', 'biometric']
    state['is_secure'] = state['lock_type'] in secure_types
    state['validation_log'] = ['Lock check performed']
    return state

def compliance_check(state: CashBoxState) -> CashBoxState:
    if not state.get('is_secure'):
        state['validation_log'].append('Security risk: non-standard lock')
    return state

graph = StateGraph(CashBoxState)
graph.add_node('validate_lock', validate_lock)
graph.add_node('compliance_check', compliance_check)
graph.set_entry_point('validate_lock')
graph.add_edge('validate_lock', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()