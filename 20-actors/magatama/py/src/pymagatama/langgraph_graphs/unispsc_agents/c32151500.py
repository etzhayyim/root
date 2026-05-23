from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ControlDeviceState(TypedDict):
    device_specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: ControlDeviceState):
    errors = []
    if 'operating_voltage' not in state['device_specs']:
        errors.append('Missing mandatory voltage specification.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: ControlDeviceState):
    return 'valid' if state['is_compliant'] else 'end'

graph = StateGraph(ControlDeviceState)
graph.add_node('validation', validate_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
