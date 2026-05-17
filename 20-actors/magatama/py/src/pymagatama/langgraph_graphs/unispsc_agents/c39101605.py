from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LampState(TypedDict):
    specs: dict
    is_compliant: bool
    disposal_plan: str

def validate_lamp(state: LampState):
    required = ['Wattage', 'Mercury Content Compliance']
    compliance = all(k in state['specs'] for k in required)
    return {'is_compliant': compliance}

def check_hazmat(state: LampState):
    return {'disposal_plan': 'Formal chemical recycling' if state['is_compliant'] else 'Rejected'}

graph = StateGraph(LampState)
graph.add_node('validate', validate_lamp)
graph.add_node('hazmat', check_hazmat)
graph.add_edge('validate', 'hazmat')
graph.add_edge('hazmat', END)
graph.set_entry_point('validate')
app = graph.compile()