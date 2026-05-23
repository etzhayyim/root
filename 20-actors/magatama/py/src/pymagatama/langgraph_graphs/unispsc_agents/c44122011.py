from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FolderState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: FolderState):
    errors = []
    if state['specifications'].get('material') not in ['Paper', 'Plastic', 'Pressboard']:
        errors.append('Invalid material type')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(FolderState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
