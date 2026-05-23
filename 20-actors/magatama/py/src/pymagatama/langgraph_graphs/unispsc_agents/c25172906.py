from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReflectorsState(TypedDict):
    part_number: str
    spec_data: dict
    is_compliant: bool

def validate_spec(state: ReflectorsState):
    """Validates compliance with automotive reflective standards."""
    compliance = state['spec_data'].get('regulatory_compliance_certification') is not None
    return {'is_compliant': compliance}

def approval_check(state: ReflectorsState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(ReflectorsState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
