from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    product_name: str
    potency: float
    storage_temp: float
    qc_passed: bool

def validate_potency(state: PharmState):
    state['qc_passed'] = 0.95 <= state['potency'] <= 1.05
    return state

def check_storage(state: PharmState):
    if state['storage_temp'] > 25:
        state['qc_passed'] = False
    return state

graph = StateGraph(PharmState)
graph.add_node('validate_potency', validate_potency)
graph.add_node('check_storage', check_storage)
graph.add_edge('validate_potency', 'check_storage')
graph.add_edge('check_storage', END)
graph.set_entry_point('validate_potency')
graph = graph.compile()
