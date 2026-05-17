from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NippleState(TypedDict):
    material: str
    compliance_docs: List[str]
    approved: bool

def validate_materials(state: NippleState):
    # Business logic for material check
    is_compliant = state['material'] in ['Silicone', 'Natural Rubber']
    return {'approved': is_compliant}

def check_certification(state: NippleState):
    # Business logic for certification audit
    has_docs = len(state['compliance_docs']) > 0
    return {'approved': state['approved'] and has_docs}

graph = StateGraph(NippleState)
graph.add_node('material_validation', validate_materials)
graph.add_node('cert_audit', check_certification)
graph.set_entry_point('material_validation')
graph.add_edge('material_validation', 'cert_audit')
graph.add_edge('cert_audit', END)
graph = graph.compile()