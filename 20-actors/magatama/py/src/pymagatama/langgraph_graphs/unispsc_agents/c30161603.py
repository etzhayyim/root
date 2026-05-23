from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CofferState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_security_rating(state: CofferState):
    errors = []
    if 'rating' not in state['spec_data']:
        errors.append('Missing security rating.')
    return {'validation_errors': errors}

def check_dimensions(state: CofferState):
    # Business logic for industrial safe procurement
    if state['spec_data'].get('weight', 0) > 500:
        print('Logistics validation: Heavy equipment handling required.')
    return {'approved': len(state['validation_errors']) == 0}

workflow = StateGraph(CofferState)
workflow.add_node('validate', validate_security_rating)
workflow.add_node('dimension_check', check_dimensions)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'dimension_check')
workflow.add_edge('dimension_check', END)
graph = workflow.compile()
