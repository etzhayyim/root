from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temperature_logs: list[float]
    is_compliant: bool

def validate_cold_chain(state: VaccineState):
    state['is_compliant'] = all(2.0 <= temp <= 8.0 for temp in state.get('temperature_logs', []))
    return state

def check_batch(state: VaccineState):
    # Simulate regulatory lookup
    state['is_compliant'] = state['is_compliant'] and (len(state['batch_id']) > 0)
    return state

graph = StateGraph(VaccineState)
graph.add_node('verify_temp', validate_cold_chain)
graph.add_node('check_batch', check_batch)
graph.set_entry_point('verify_temp')
graph.add_edge('verify_temp', 'check_batch')
graph.add_edge('check_batch', END)
graph = graph.compile()
