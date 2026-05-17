from typing import TypedDict
from langgraph.graph import StateGraph, END

class CalculationDeviceState(TypedDict):
    device_spec: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CalculationDeviceState):
    device = state['device_spec']
    errors = []
    if not device.get('digit_capacity', 0) >= 10:
        errors.append('Insufficient digit capacity for accounting tasks')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: CalculationDeviceState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(CalculationDeviceState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()