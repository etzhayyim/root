from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_sensor_specs(state: SensorState):
    errors = []
    if state['spec_data'].get('sensitivity', 0) <= 0:
        errors.append('Invalid sensitivity value')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(SensorState)
graph.add_node('validate', validate_sensor_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
