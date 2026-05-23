from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CurriculumState(TypedDict):
    book_title: str
    target_grade: str
    compliance_checked: bool
    validation_errors: List[str]

def validate_curriculum(state: CurriculumState):
    errors = []
    if not state.get('target_grade'):
        errors.append('Target grade missing')
    return {'validation_errors': errors, 'compliance_checked': len(errors) == 0}

def format_output(state: CurriculumState):
    return {'book_title': f'Validated: {state['book_title']}'}

graph = StateGraph(CurriculumState)
graph.add_node('validate', validate_curriculum)
graph.add_node('format', format_output)
graph.add_edge('validate', 'format')
graph.add_edge('format', END)
graph.set_entry_point('validate')
graph = graph.compile()
