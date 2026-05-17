from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalStoolState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_medical_grade(state: SurgicalStoolState):
    errors = []
    if state['specifications'].get('load_capacity', 0) < 150:
        errors.append('Load capacity below clinical safety threshold.')
    if not state['specifications'].get('is_conductive'):
        errors.append('Missing conductive material certification.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(SurgicalStoolState)
graph.add_node('validate', validate_medical_grade)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()