from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HUDProcurementState(TypedDict):
    part_number: str
    compliance_certs: List[str]
    export_license_required: bool
    approved: bool

def validate_specs(state: HUDProcurementState):
    required = {'RTCA-DO-178C', 'MIL-STD-810'}
    state['approved'] = all(cert in state['compliance_certs'] for cert in required)
    return state

def check_export_controls(state: HUDProcurementState):
    if state.get('export_license_required', False):
        print('Regulatory hold: Export license verification required.')
    return state

graph = StateGraph(HUDProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()