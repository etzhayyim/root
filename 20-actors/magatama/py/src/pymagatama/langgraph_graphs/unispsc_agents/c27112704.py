from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    specs: dict
    approved: bool

def validate_safety_certs(state: ToolState):
    certs = state['specs'].get('safety_certification', [])
    state['approved'] = 'CE' in certs or 'UL' in certs
    return state

def check_power_requirements(state: ToolState):
    if state['specs'].get('motor_wattage', 0) > 2000:
        print('High power tool approval required.')
    return state

graph = StateGraph(ToolState)
graph.add_node('safety', validate_safety_certs)
graph.add_node('power_check', check_power_requirements)
graph.set_entry_point('safety')
graph.add_edge('safety', 'power_check')
graph.add_edge('power_check', END)
graph = graph.compile()