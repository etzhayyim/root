from typing import TypedDict
from langgraph.graph import StateGraph, END

class LampState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: LampState) -> LampState:
    required = ['Voltage', 'Wattage', 'Diameter']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def check_certification(state: LampState) -> LampState:
    if state.get('is_compliant'):
        state['is_compliant'] = 'Compliance Certification' in state['specs']
    return state

graph = StateGraph(LampState)
graph.add_node("validate", validate_specs)
graph.add_node("certify", check_certification)
graph.set_entry_point("validate")
graph.add_edge("validate", "certify")
graph.add_edge("certify", END)
app = graph.compile()
