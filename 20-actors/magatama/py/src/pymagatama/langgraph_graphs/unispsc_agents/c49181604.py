from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DartSpecs(TypedDict):
    weight: float
    material: str
    is_safe_tip: bool

class State(TypedDict):
    specs: DartSpecs
    validated: bool
    errors: List[str]

def validate_specs(state: State):
    specs = state['specs']
    errors = []
    if specs['weight'] > 50.0:
        errors.append('Weight exceeds competition limit')
    
    return {'validated': len(errors) == 0, 'errors': errors}

workflow = StateGraph(State)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()