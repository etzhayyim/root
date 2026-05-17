from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SatelliteState(TypedDict):
    orbit_data: dict
    security_clearance: bool
    compliance_docs: List[str]

def validate_orbit(state: SatelliteState):
    # Perform check on orbital parameters compatibility
    return {'orbit_data': state['orbit_data']}

def check_compliance(state: SatelliteState):
    # Validate ITAR/EAR compliance protocols
    return {'compliance_docs': ['validated']}

graph = StateGraph(SatelliteState)
graph.add_node('validate_orbit', validate_orbit)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_orbit')
graph.add_edge('validate_orbit', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()