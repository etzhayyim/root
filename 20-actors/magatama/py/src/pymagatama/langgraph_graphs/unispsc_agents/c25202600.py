from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AircraftControlState(TypedDict):
    part_number: str
    spec_requirements: List[str]
    compliance_validated: bool
    export_license_required: bool

def validate_specs(state: AircraftControlState):
    state['compliance_validated'] = all(req in state['spec_requirements'] for req in ['AS9100', 'RTCA-DO-160'])
    return state

def check_dual_use(state: AircraftControlState):
    state['export_license_required'] = True
    return state

graph = StateGraph(AircraftControlState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
