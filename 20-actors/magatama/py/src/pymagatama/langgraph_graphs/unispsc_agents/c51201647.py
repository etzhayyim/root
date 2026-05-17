from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temp_log: list
    is_compliant: bool

def validate_cold_chain(state: VaccineState) -> VaccineState:
    # Logic to verify temperature logs for cold chain integrity
    state['is_compliant'] = all(t < 8.0 for t in state['temp_log'])
    return state

def check_regulatory(state: VaccineState) -> VaccineState:
    # Logic for batch regulatory check
    return state

graph = StateGraph(VaccineState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('check_regulatory', check_regulatory)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'check_regulatory')
graph.add_edge('check_regulatory', END)
graph = graph.compile()