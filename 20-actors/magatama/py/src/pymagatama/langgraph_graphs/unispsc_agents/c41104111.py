from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CytologyState(TypedDict):
    product_specs: dict
    compliance_checks: List[str]
    validation_status: str

def validate_medical_compliance(state: CytologyState):
    checks = state['compliance_checks']
    if 'ISO13485' in state['product_specs'].get('certs', []):
        checks.append('Compliance Passed')
    else:
        checks.append('Compliance Failed')
    return {'compliance_checks': checks, 'validation_status': 'verified'}

def route_verification(state: CytologyState):
    if state['validation_status'] == 'verified':
        return 'END'
    return 'END'

graph = StateGraph(CytologyState)
graph.add_node('compliance', validate_medical_compliance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', END)