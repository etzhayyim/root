from typing import TypedDict
from langgraph.graph import StateGraph, END

class RelayState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: RelayState):
    required = ['coil_voltage', 'contact_configuration']
    errors = [f'missing {f}' for f in required if f not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: RelayState):
    return 'valid' if state['validation_passed'] else 'invalid'

graph = StateGraph(RelayState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
