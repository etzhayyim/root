from typing import TypedDict
from langgraph.graph import StateGraph, END

class ImpactTesterState(TypedDict):
    spec_data: dict
    validation_passed: bool
    calibration_status: str

def validate_specs(state: ImpactTesterState):
    energy = state['spec_data'].get('impact_energy_joules', 0)
    return {'validation_passed': energy > 0, 'calibration_status': 'pending'}

def check_certification(state: ImpactTesterState):
    return {'calibration_status': 'verified' if 'iso' in state['spec_data'].get('calibration_standard_iso', '').lower() else 'failed'}

graph = StateGraph(ImpactTesterState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()