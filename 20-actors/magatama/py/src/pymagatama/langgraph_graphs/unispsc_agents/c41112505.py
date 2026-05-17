from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterMeterState(TypedDict):
    part_number: str
    compatibility_verified: bool
    pressure_rating: float
    status: str

def verify_compatibility(state: WaterMeterState):
    state['compatibility_verified'] = state['part_number'].startswith('WM-')
    state['status'] = 'verified' if state['compatibility_verified'] else 'rejected'
    return state

def check_pressure(state: WaterMeterState):
    if state['pressure_rating'] < 10.0:
        state['status'] = 'pressure_insufficient'
    return state

graph = StateGraph(WaterMeterState)
graph.add_node('verify', verify_compatibility)
graph.add_node('pressure_check', check_pressure)
graph.set_entry_point('verify')
graph.add_edge('verify', 'pressure_check')
graph.add_edge('pressure_check', END)
app = graph.compile()