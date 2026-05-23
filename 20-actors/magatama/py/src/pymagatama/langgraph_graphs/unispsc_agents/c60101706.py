from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CurriculumState(TypedDict):
    content: dict
    validation_errors: List[str]
    approved: bool

def validate_curriculum(state: CurriculumState):
    errors = []
    if not state['content'].get('version'): errors.append('Missing version')
    if not state['content'].get('grade'): errors.append('Missing grade level')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

workflow = StateGraph(CurriculumState)
workflow.add_node('validator', validate_curriculum)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()
