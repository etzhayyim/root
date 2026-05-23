from langgraph.graph import StateGraph, END
from typing import TypedDict

class RefrigeratorState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: RefrigeratorState):
    errors = []
    if state['specs'].get('energy_rating', 'G') == 'G':
        errors.append('Energy efficiency below acceptable threshold.')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def finalize_procurement(state: RefrigeratorState):
    return {'status': 'Approved' if state['validation_passed'] else 'Rejected'}

workflow = StateGraph(RefrigeratorState)
workflow.add_node('validate', validate_specs)
workflow.add_node('finalize', finalize_procurement)
workflow.add_edge('validate', 'finalize')
workflow.set_entry_point('validate')
workflow.add_edge('finalize', END)
graph = workflow.compile()
