from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenApplianceState(TypedDict):
    model_number: str
    safety_certs: list[str]
    voltage_check: bool
    approved: bool

def validate_safety(state: KitchenApplianceState):
    state['approved'] = 'UL' in state['safety_certs'] or 'CE' in state['safety_certs']
    return state

def check_voltage(state: KitchenApplianceState):
    state['voltage_check'] = True
    return state

graph = StateGraph(KitchenApplianceState)
graph.add_node('safety_check', validate_safety)
graph.add_node('voltage_check', check_voltage)
graph.add_edge('safety_check', 'voltage_check')
graph.add_edge('voltage_check', END)
graph.set_entry_point('safety_check')
graph = graph.compile()