from typing import TypedDict
from langgraph.graph import StateGraph, END

class SplintState(TypedDict):
    material_type: str
    compliance_docs: list
    is_molding_compatible: bool

def validate_materials(state: SplintState):
    # Simulate CAD/Spec validation for medical splinting materials
    state['is_molding_compatible'] = True if 'thermoplastic' in state['material_type'].lower() else False
    return state

workflow = StateGraph(SplintState)
workflow.add_node('validate', validate_materials)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
