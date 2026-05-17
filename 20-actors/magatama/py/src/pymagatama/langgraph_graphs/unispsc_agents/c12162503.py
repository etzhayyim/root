from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ConductiveMaterialState(TypedDict):
    material_id: str
    purity_level: float
    conductivity: float
    is_verified: bool
    compliance_tags: List[str]

def validate_material(state: ConductiveMaterialState):
    if state['purity_level'] >= 99.9 and state['conductivity'] >= 1000:
        return {'is_verified': True, 'compliance_tags': ['passed_qc']}
    return {'is_verified': False, 'compliance_tags': ['failed_qc']}

def update_compliance(state: ConductiveMaterialState):
    tags = state.get('compliance_tags', [])
    if state['is_verified']:
        tags.append('cleared_for_production')
    return {'compliance_tags': tags}

graph = StateGraph(ConductiveMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', update_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()