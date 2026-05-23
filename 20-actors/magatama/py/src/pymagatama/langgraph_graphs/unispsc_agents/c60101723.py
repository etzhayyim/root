from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SeatingState(TypedDict):
    layout_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_layout(state: SeatingState):
    errors = []
    if not state['layout_data'].get('capacity'):
        errors.append('Invalid capacity')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(SeatingState)
graph.add_node('validate', validate_layout)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
