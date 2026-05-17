from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ContainerState(TypedDict):
    container_id: str
    spec_sheet_url: str
    compliance_checks: List[str]
    is_approved: bool

def validate_sterilization_specs(state: ContainerState):
    # Simulate validation logic for container materials and filter efficiency
    checks = []
    if 'ISO11607' in state['spec_sheet_url']:
        checks.append('Compliance Passed: ISO 11607')
    return {'compliance_checks': checks, 'is_approved': len(checks) > 0}

def route_by_compliance(state: ContainerState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ContainerState)
graph.add_node('validate', validate_sterilization_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()