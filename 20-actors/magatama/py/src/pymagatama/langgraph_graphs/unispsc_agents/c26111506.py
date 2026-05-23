from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MotionDeviceState(TypedDict):
    device_spec: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: MotionDeviceState):
    errors = []
    if state['device_spec'].get('repeatability_accuracy_microns', 0) > 50:
        errors.append('Accuracy exceeds industrial automation tolerance limits.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(MotionDeviceState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
