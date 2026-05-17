from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScaffoldingState(TypedDict):
    load_capacity: float
    safety_certs: list[str]
    compliance_report: str

def validate_load_specs(state: ScaffoldingState):
    is_safe = state['load_capacity'] >= 500
    return {'compliance_report': 'Passed' if is_safe else 'Failed: Load capacity insufficient'}

def check_certifications(state: ScaffoldingState):
    has_min_certs = len(state['safety_certs']) >= 2
    return {'compliance_report': 'Passed' if has_min_certs else 'Failed: Missing mandatory certifications'}

graph = StateGraph(ScaffoldingState)
graph.add_node('validate', validate_load_specs)
graph.add_node('certify', check_certifications)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()