from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BeltSpecState(TypedDict):
    specs: dict
    validated: bool
    errors: List[str]

def validate_specs(state: BeltSpecState):
    required = ['material', 'dimensions', 'model_code']
    errors = []
    for field in required:
        if field not in state['specs']:
            errors.append(f'Missing {field}')
    return {'validated': len(errors) == 0, 'errors': errors}

def route_by_validation(state: BeltSpecState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(BeltSpecState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')