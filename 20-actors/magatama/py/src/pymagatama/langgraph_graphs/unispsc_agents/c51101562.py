from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class DiagnosticState(TypedDict):
    commodity_code: str
    batch_id: str
    temperature_logs: list[float]
    status: str

def validate_cold_chain(state: DiagnosticState) -> DiagnosticState:
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs']) if state['temperature_logs'] else 25.0
    if 2.0 <= avg_temp <= 8.0:
        state['status'] = 'COMPLIANT'
    else:
        state['status'] = 'EXCURSION_RISK'
    return state

def verify_expiry(state: DiagnosticState) -> DiagnosticState:
    if state['status'] == 'COMPLIANT':
        state['status'] = 'VALIDATED'
    return state

graph = StateGraph(DiagnosticState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('verify_expiry', verify_expiry)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'verify_expiry')
graph.add_edge('verify_expiry', END)
graph = graph.compile()