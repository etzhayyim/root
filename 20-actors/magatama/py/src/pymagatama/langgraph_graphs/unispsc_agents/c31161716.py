from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LocknutState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: LocknutState):
    errors = []
    if not state['spec_data'].get('material'): errors.append('Missing material')
    if not state['spec_data'].get('torque'): errors.append('Missing torque data')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_compliance(state: LocknutState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(LocknutState)
graph.add_node('validate', validate_specs)
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph.set_entry_point('validate')
graph = graph.compile()
