from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalSpecState(TypedDict):
    item_id: str
    specs: dict
    is_validated: bool
    validation_errors: List[str]

def validate_medical_specs(state: SurgicalSpecState):
    required = ['material_composition', 'sterilization_method']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'is_validated': len(errors) == 0, 'validation_errors': errors}

def route_by_validation(state: SurgicalSpecState):
    return 'APPROVED' if state['is_validated'] else 'REJECTED'

graph = StateGraph(SurgicalSpecState)
graph.add_node('validate', validate_medical_specs)
graph.add_conditional_edges('validate', route_by_validation, {'APPROVED': END, 'REJECTED': END})
graph.set_entry_point('validate')
graph = graph.compile()