from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PinState(TypedDict):
    part_number: str
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: PinState):
    errors = []
    if state['specifications'].get('taper_ratio', '') != '1:50':
        errors.append('Invalid taper ratio for standard application.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(PinState)
graph.add_node('validate', validate_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
