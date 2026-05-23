from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalUnitState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_medical_standards(state: SurgicalUnitState):
    """Verify device against regulatory standards."""
    cert = state['specs'].get('certification')
    if not cert:
        state['validation_errors'].append('Missing certification')
    return {'is_compliant': bool(cert)}

def compile_procurement_workflow():
    graph = StateGraph(SurgicalUnitState)
    graph.add_node('validate', validate_medical_standards)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = compile_procurement_workflow()
