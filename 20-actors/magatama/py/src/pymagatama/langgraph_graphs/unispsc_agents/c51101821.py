from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    gmp_status: bool
    coa_valid: bool
    steps: list

def check_compliance(state: ProcurementState):
    is_compliant = state['gmp_status'] and state['coa_valid']
    return {'steps': state['steps'] + ['compliance_check_passed'] if is_compliant else ['compliance_failure']}

def update_logistics(state: ProcurementState):
    return {'steps': state['steps'] + ['logistics_route_assigned']}

graph = StateGraph(ProcurementState)
graph.add_node('compliance', check_compliance)
graph.add_node('logistics', update_logistics)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()