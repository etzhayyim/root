from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class JewelryState(TypedDict):
    material_specs: str
    safety_certs: List[str]
    is_compliant: bool

def validate_material(state: JewelryState):
    compliant = 'Titanium' in state['material_specs'] or 'Steel' in state['material_specs']
    return {'is_compliant': compliant}

def check_certs(state: JewelryState):
    return {'is_compliant': state['is_compliant'] and len(state['safety_certs']) > 0}

graph = StateGraph(JewelryState)
graph.add_node('material_check', validate_material)
graph.add_node('cert_check', check_certs)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'cert_check')
graph.add_edge('cert_check', END)
graph = graph.compile()
