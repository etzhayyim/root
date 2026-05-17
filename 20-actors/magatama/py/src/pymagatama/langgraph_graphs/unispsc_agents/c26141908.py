from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlowSystemState(TypedDict):
    source_activity: float
    license_validated: bool
    safety_check: bool

def validate_safety_protocols(state: FlowSystemState):
    if state['source_activity'] > 0:
        return {'safety_check': True}
    return {'safety_check': False}

def verify_regulatory_license(state: FlowSystemState):
    return {'license_validated': True}

graph = StateGraph(FlowSystemState)
graph.add_node('safety_check', validate_safety_protocols)
graph.add_node('license_check', verify_regulatory_license)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'license_check')
graph.add_edge('license_check', END)
graph = graph.compile()