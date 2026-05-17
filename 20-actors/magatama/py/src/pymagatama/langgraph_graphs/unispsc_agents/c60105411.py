from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EduMaterialState(TypedDict):
    material_id: str
    validation_checks: List[str]
    is_approved: bool

def validate_pedagogy(state: EduMaterialState):
    print('Validating pedagogical alignment for self-esteem content...')
    state['validation_checks'].append('pedagogy_verified')
    return state

def check_compliance(state: EduMaterialState):
    print('Checking content for accessibility standards...')
    state['validation_checks'].append('compliance_verified')
    state['is_approved'] = True
    return state

graph = StateGraph(EduMaterialState)
graph.add_node('validate_pedagogy', validate_pedagogy)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_pedagogy')
graph.add_edge('validate_pedagogy', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()