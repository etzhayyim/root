from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NickelProcurementState(TypedDict):
    material_specs: dict
    compliance_checks: List[str]
    approved: bool

def validate_specs(state: NickelProcurementState):
    checks = []
    if state['material_specs'].get('purity_percentage', 0) >= 99.0:
        checks.append('Purity Check Passed')
    return {'compliance_checks': checks, 'approved': len(checks) > 0}

def approval_logic(state: NickelProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(NickelProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
