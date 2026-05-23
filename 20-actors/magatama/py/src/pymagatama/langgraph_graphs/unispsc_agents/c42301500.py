from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TrainingAidState(TypedDict):
    item_id: str
    specs: dict
    is_validated: bool
    validation_errors: List[str]

def validate_specs(state: TrainingAidState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material info')
    return {'is_validated': len(errors) == 0, 'validation_errors': errors}

def route_by_validation(state: TrainingAidState):
    return 'validate' if not state.get('is_validated') else END

graph = StateGraph(TrainingAidState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

graph = graph.compile()
