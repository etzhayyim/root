from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BEMSState(TypedDict):
    requirements: dict
    validation_checks: List[str]
    approved: bool

def validate_efficiency(state: BEMSState):
    checks = state.get('validation_checks', [])
    if state['requirements'].get('energy_rating') == 'A':
        checks.append('Efficiency Verified')
    return {'validation_checks': checks}

def check_compliance(state: BEMSState):
    checks = state.get('validation_checks', [])
    if 'BMS-Protocol-ISO' in state['requirements'].get('protocols', []):
        checks.append('Protocol Compliant')
    return {'validation_checks': checks, 'approved': True}

graph = StateGraph(BEMSState)
graph.add_node('validate_efficiency', validate_efficiency)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_efficiency')
graph.add_edge('validate_efficiency', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
