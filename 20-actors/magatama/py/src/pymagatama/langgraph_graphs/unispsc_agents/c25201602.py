from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftNavState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_specs(state: AircraftNavState):
    specs = state['spec_data']
    valid = 'FAA_TSO_compliance' in specs and 'DO-160' in specs['environmental']
    return {'validated': valid, 'compliance_report': 'Success' if valid else 'Validation Failed'}

def route_by_compliance(state: AircraftNavState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(AircraftNavState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
