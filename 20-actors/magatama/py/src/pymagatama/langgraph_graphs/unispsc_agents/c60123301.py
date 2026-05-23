from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
class CraftMaterialState(TypedDict):
    material_type: str
    quality_check_passed: bool
    compliance_report: str
def validate_acrylic_specs(state: CraftMaterialState):
    state['quality_check_passed'] = state['material_type'] == 'acrylic'
    state['compliance_report'] = 'Standard compliance check complete.'
    return state
graph = StateGraph(CraftMaterialState)
graph.add_node('validate', validate_acrylic_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
