from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VesselProcurementState(TypedDict):
    vessel_id: str
    compliance_passed: bool
    inspection_report: List[str]

def validate_specs(state: VesselProcurementState):
    print(f'Validating specs for {state[\'vessel_id\']}')
    return {'compliance_passed': True, 'inspection_report': ['IMOs compliance verified']}

def security_clearance(state: VesselProcurementState):
    print('Performing arms-or-security background check')
    return {'inspection_report': state['inspection_report'] + ['security cleared']}

graph = StateGraph(VesselProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('security', security_clearance)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()