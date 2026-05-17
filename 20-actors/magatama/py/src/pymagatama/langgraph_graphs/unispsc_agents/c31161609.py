from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToggleBoltState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_bolt_specs(state: ToggleBoltState):
    errors = []
    required = ['material', 'load_capacity', 'finish']
    for field in required:
        if field not in state['spec_data']:
            errors.append(f'Missing field: {field}')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def structural_integrity_check(state: ToggleBoltState):
    if state['spec_data'].get('load_capacity', 0) < 50:
        return {'validation_passed': False, 'errors': ['Insufficient load capacity for standard use']}
    return {'validation_passed': True}

graph = StateGraph(ToggleBoltState)
graph.add_node('validate', validate_bolt_specs)
graph.add_node('integrity', structural_integrity_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrity')
graph.add_edge('integrity', END)

graph = graph.compile()