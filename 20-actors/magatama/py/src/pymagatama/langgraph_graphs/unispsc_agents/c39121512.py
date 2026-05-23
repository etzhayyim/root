from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: SwitchState):
    required = ['Rated Voltage', 'Rated Current', 'Mounting Hole Diameter']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def check_ip_rating(state: SwitchState):
    if state['specs'].get('IP Rating', 0) < 54:
        state['is_compliant'] = False
    return state

graph = StateGraph(SwitchState)
graph.add_node('validate', validate_specs)
graph.add_node('ip_check', check_ip_rating)
graph.set_entry_point('validate')
graph.add_edge('validate', 'ip_check')
graph.add_edge('ip_check', END)
graph = graph.compile()
