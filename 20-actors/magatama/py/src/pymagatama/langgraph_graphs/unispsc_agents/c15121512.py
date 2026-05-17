from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class HoseProcurementState(TypedDict):
    spec_requirements: dict
    validation_checks: List[str]
    compliance_status: bool

def validate_specs(state: HoseProcurementState):
    checks = []
    if state['spec_requirements'].get('pressure_rating', 0) > 5000:
        checks.append('High-Pressure Validation Required')
    return {'validation_checks': checks}

def compliance_review(state: HoseProcurementState):
    return {'compliance_status': True}

graph = StateGraph(HoseProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_review)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()