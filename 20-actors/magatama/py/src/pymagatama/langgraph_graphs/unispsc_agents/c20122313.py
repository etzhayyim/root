from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_sensor_specs(state: SensorState):
    errors = []
    if state['spec_data'].get('ip_rating', 0) < 65:
        errors.append('Insufficient IP rating for industrial environment')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def compile_sensor_workflow():
    workflow = StateGraph(SensorState)
    workflow.add_node('validate', validate_sensor_specs)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', END)
    return workflow.compile()

graph = compile_sensor_workflow()