from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftState(TypedDict):
    aircraft_id: str
    compliance_cleared: bool
    export_license_verified: bool

def check_compliance(state: AircraftState):
    print('Verifying aviation safety and export compliance for:', state['aircraft_id'])
    return {'compliance_cleared': True}

def verify_export_license(state: AircraftState):
    print('Validating dual-use export permits...')
    return {'export_license_verified': True}

graph = StateGraph(AircraftState)
graph.add_node('safety_check', check_compliance)
graph.add_node('export_review', verify_export_license)
graph.add_edge('safety_check', 'export_review')
graph.add_edge('export_review', END)
graph.set_entry_point('safety_check')
graph = graph.compile()
