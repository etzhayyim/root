from typing import TypedDict
from langgraph.graph import StateGraph, END

class RelayState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: RelayState):
    required = ['rated_voltage', 'phase_type']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_passed': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: RelayState):
    return 'process' if state['validation_passed'] else 'flag_error'

graph = StateGraph(RelayState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END, 'flag_error': END})
graph.compile()
