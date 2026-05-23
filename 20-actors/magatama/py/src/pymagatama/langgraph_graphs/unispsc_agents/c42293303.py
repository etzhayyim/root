from typing import TypedDict
from langgraph.graph import StateGraph, END
class SurgicalSpeculaState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool
def validate_materials(state: SurgicalSpeculaState):
    material = state['spec_data'].get('material_grade')
    return {'validation_results': ['Material compliance: ' + str(material == '316L')]}
def validate_regulatory(state: SurgicalSpeculaState):
    clearance = state['spec_data'].get('regulatory_clearance_number')
    return {'validation_results': state['validation_results'] + ['Regulatory check: ' + str(bool(clearance))]}
builder = StateGraph(SurgicalSpeculaState)
builder.add_node('material_check', validate_materials)
builder.add_node('regulatory_check', validate_regulatory)
builder.set_entry_point('material_check')
builder.add_edge('material_check', 'regulatory_check')
builder.add_edge('regulatory_check', END)
graph = builder.compile()
