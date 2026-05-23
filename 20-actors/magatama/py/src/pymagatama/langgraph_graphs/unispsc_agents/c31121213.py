from langgraph.graph import StateGraph, END
from typing import TypedDict

class CastingState(TypedDict):
    part_specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CastingState):
    specs = state['part_specs']
    errors = []
    if specs.get('tolerance', 0.0) > 0.05:
        errors.append('Tolerance exceeds precision threshold')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def approval_step(state: CastingState):
    return {'validation_passed': True}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
