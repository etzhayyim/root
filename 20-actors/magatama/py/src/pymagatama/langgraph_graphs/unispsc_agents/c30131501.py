from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CementState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: CementState):
    errors = []
    if state['specs'].get('compressive_strength_mpa', 0) < 15:
        errors.append('Strength below standard requirements')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approval_step(state: CementState):
    print('Proceeding with procurement approval...')
    return {}

graph = StateGraph(CementState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
