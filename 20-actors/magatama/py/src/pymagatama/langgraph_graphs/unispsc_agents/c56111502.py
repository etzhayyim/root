from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FurnitureState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: FurnitureState):
    errors = []
    if not state['specs'].get('fire_retardancy_standard'):
        errors.append('Missing fire safety certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def process_procurement(state: FurnitureState):
    return {'is_compliant': True}

workflow = StateGraph(FurnitureState)
workflow.add_node('validate', validate_specs)
workflow.add_node('process', process_procurement)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'process')
workflow.add_edge('process', END)
graph = workflow.compile()
