from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EducationMaterialState(TypedDict):
    product_name: str
    age_appropriateness: int
    safety_certs: List[str]
    validation_status: bool

def validate_material(state: EducationMaterialState):
    is_safe = all(cert in state['safety_certs'] for cert in ['ASTM-F963', 'EN71'])
    print(f'Validating material: {state[product_name]}')
    return {'validation_status': is_safe}

graph = StateGraph(EducationMaterialState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
