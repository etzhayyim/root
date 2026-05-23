from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BoltState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: List[str]

def validate_bolt_specs(state: BoltState):
    specs = state['spec_data']
    errors = []
    if 'tensile_strength' not in specs: errors.append('Missing tensile strength')
    if 'material' not in specs: errors.append('Missing material info')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: BoltState):
    return 'valid' if state['validation_passed'] else 'invalid'

workflow = StateGraph(BoltState)
workflow.add_node('validate', validate_bolt_specs)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', route_by_validation, {'valid': END, 'invalid': END})
graph = workflow.compile()
