from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExerciseBallState(TypedDict):
    spec_requirements: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_ball_specs(state: ExerciseBallState):
    errors = []
    if state['spec_requirements'].get('max_weight', 0) < 100:
        errors.append('Weight capacity below industry commercial standards.')
    if not state['spec_requirements'].get('anti_burst', False):
        errors.append('Anti-burst certification missing.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(ExerciseBallState)
graph.add_node('validate', validate_ball_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
