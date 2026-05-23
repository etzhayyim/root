from typing import TypedDict
from langgraph.graph import StateGraph, END

class KVPState(TypedDict):
    voltage_input: float
    calibrated: bool
    safety_verified: bool

def validate_meter_input(state: KVPState):
    state['calibrated'] = state['voltage_input'] > 0
    return state

def verify_safety_standards(state: KVPState):
    state['safety_verified'] = True if state['calibrated'] else False
    return state

graph = StateGraph(KVPState)
graph.add_node('validate', validate_meter_input)
graph.add_node('safety', verify_safety_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
