from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OccluderState(TypedDict):
    material: str
    is_medical_grade: bool
    validation_errors: List[str]

def validate_material(state: OccluderState):
    if state['material'] not in ['Medical Grade Plastic', 'Stainless Steel']:
        state['validation_errors'].append('Non-compliant material')
    return state

def check_compliance(state: OccluderState):
    return 'pass' if state['is_medical_grade'] and not state['validation_errors'] else 'fail'

graph = StateGraph(OccluderState)
graph.add_node('validate', validate_material)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
