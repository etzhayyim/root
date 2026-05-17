from typing import TypedDict
from langgraph.graph import StateGraph, END

class RoadState(TypedDict):
    pavement_specs: dict
    compliance_report: str
    approval_status: bool

def validate_materials(state: RoadState):
    # Simulate material compliance check for ring road construction
    state['approval_status'] = 'durability' in state['pavement_specs']
    return state

def sign_off(state: RoadState):
    return {'compliance_report': 'Validated' if state['approval_status'] else 'Rejected'}

graph = StateGraph(RoadState)
graph.add_node('validate', validate_materials)
graph.add_node('sign_off', sign_off)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sign_off')
graph.add_edge('sign_off', END)
graph = graph.compile()