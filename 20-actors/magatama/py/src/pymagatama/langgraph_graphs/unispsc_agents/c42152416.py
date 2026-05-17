from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalMaterialState(TypedDict):
    material_type: str
    quality_check: bool
    compliance_verified: bool

def validate_material(state: DentalMaterialState):
    print(f'Validating material: {state[\'material_type\']}')
    return {'compliance_verified': True}

def check_quality(state: DentalMaterialState):
    return {'quality_check': state['compliance_verified']}

graph = StateGraph(DentalMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('qc', check_quality)
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph.set_entry_point('validate')
graph = graph.compile()