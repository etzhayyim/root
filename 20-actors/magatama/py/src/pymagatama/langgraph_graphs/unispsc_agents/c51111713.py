from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlemtuzumabState(TypedDict):
    vial_barcode: str
    temperature_logs: list[float]
    verification_status: bool

def validate_cold_chain(state: AlemtuzumabState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs'])
    status = 2.0 <= avg_temp <= 8.0
    return {'verification_status': status}

def verify_integrity(state: AlemtuzumabState):
    return {'verification_status': state['verification_status'] and len(state['vial_barcode']) == 12}

graph = StateGraph(AlemtuzumabState)
graph.add_node('validate_temp', validate_cold_chain)
graph.add_node('verify_code', verify_integrity)
graph.set_entry_point('validate_temp')
graph.add_edge('validate_temp', 'verify_code')
graph.add_edge('verify_code', END)
graph = graph.compile()