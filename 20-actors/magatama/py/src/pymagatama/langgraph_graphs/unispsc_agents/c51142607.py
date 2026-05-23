from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    license_valid: bool
    compliance_docs: List[str]
    hazard_check: bool

def validate_license(state: ProcurementState):
    state['license_valid'] = True
    return 'check_compliance'

def check_compliance(state: ProcurementState):
    state['compliance_docs'] = ['Form-Narc-01', 'Export-Auth-99']
    return 'finalize_procurement'

def finalize_procurement(state: ProcurementState):
    state['hazard_check'] = True
    return END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_license)
graph.add_node('check_compliance', check_compliance)
graph.add_node('finalize_procurement', finalize_procurement)
graph.add_edge('validate', 'check_compliance')
graph.add_edge('check_compliance', 'finalize_procurement')
graph.set_entry_point('validate')
