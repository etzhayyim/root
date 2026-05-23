from typing import TypedDict
from langgraph.graph import StateGraph, END
class TitaniumState(TypedDict):
    material_grade: str
    compliance_docs: list
    is_approved: bool
def validate_specs(state: TitaniumState):
    required = ['ASTM_B381', 'AMS_4928']
    passed = state['material_grade'] in required
    return {'is_approved': passed}
def check_certs(state: TitaniumState):
    has_certs = len(state.get('compliance_docs', [])) >= 3
    return {'is_approved': state['is_approved'] and has_certs}
graph = StateGraph(TitaniumState)
graph.add_node('validate', validate_specs)
graph.add_node('certs', check_certs)
graph.add_edge('validate', 'certs')
graph.add_edge('certs', END)
graph.set_entry_point('validate')
graph = graph.compile()
