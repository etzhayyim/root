from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AircraftPowerState(TypedDict):
    specs: dict
    compliance_check: bool
    export_control_status: str

def validate_specs(state: AircraftPowerState):
    required = ['TSO_certification', 'emi_emc_compliance']
    state['compliance_check'] = all(k in state['specs'] for k in required)
    return state

def check_export_laws(state: AircraftPowerState):
    state['export_control_status'] = 'Flagged' if state['compliance_check'] else 'Blocked'
    return state

graph = StateGraph(AircraftPowerState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export_laws)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()
