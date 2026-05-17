from typing import TypedDict
from langgraph.graph import StateGraph, END

class BookCuttingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_tech_specs(state: BookCuttingState):
    required = ['blade_material', 'safety_rating']
    errors = []
    for field in required:
        if field not in state['spec_data']: errors.append(f'Missing {field}')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: BookCuttingState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(BookCuttingState)
graph.add_node('validate', validate_tech_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()