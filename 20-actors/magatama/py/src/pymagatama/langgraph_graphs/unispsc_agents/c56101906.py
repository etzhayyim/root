from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TableExtensionState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: TableExtensionState):
    """Validates dimensional compatibility."""
    errors = []
    if state['specs'].get('width', 0) <= 0:
        errors.append('Invalid width')
    return {'validation_errors': errors}

def final_check(state: TableExtensionState):
    """Checks if all validation tests passed."""
    is_valid = len(state['validation_errors']) == 0
    return {'is_approved': is_valid}

graph = StateGraph(TableExtensionState)
graph.add_node('validate', validate_dimensions)
graph.add_node('approve', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
