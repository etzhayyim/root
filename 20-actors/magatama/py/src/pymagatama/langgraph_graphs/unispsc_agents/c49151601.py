from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PuckState(TypedDict):
    puck_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_physics(state: PuckState):
    specs = state['puck_specs']
    errors = []
    if not (156 <= specs.get('weight', 0) <= 170):
        errors.append('Weight out of official range')
    if not (2.5 <= specs.get('thickness', 0) <= 2.54):
        errors.append('Thickness out of official range')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(PuckState)
graph.add_node('validate', validate_physics)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()