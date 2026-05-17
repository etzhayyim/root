from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DoorSurroundState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: DoorSurroundState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material')
    if 'fire_rating' not in state['specs']: errors.append('Missing fire rating')
    return {**state, 'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(DoorSurroundState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()