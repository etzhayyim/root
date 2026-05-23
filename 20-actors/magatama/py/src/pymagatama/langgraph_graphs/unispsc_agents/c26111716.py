from typing import TypedDict
from langgraph.graph import StateGraph, END

class BatteryState(TypedDict):
    battery_type: str
    compliance_checked: bool
    hazmat_cleared: bool

def validate_battery_chemistry(state: BatteryState):
    state['compliance_checked'] = state['battery_type'] == 'mercury_oxide'
    return state

def check_hazmat_docs(state: BatteryState):
    state['hazmat_cleared'] = True
    return state

graph = StateGraph(BatteryState)
graph.add_node('validate', validate_battery_chemistry)
graph.add_node('hazmat_verify', check_hazmat_docs)
graph.add_edge('validate', 'hazmat_verify')
graph.add_edge('hazmat_verify', END)
graph.set_entry_point('validate')
graph = graph.compile()
