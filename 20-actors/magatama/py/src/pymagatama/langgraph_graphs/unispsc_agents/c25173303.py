from typing import TypedDict
from langgraph.graph import StateGraph, END

class AutomotiveSystemState(TypedDict):
    part_id: str
    safety_level: str
    compliance_verified: bool

def validate_safety_protocols(state: AutomotiveSystemState):
    state['compliance_verified'] = state['safety_level'] in ['ASIL-A', 'ASIL-B', 'ASIL-C', 'ASIL-D']
    return state

def route_to_testing(state: AutomotiveSystemState):
    return 'testing' if state['compliance_verified'] else END

graph = StateGraph(AutomotiveSystemState)
graph.add_node('validate', validate_safety_protocols)
graph.add_node('testing', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_to_testing)
graph.add_edge('testing', END)
graph = graph.compile()
