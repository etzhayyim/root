from typing import TypedDict
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list

def validate_thermal_specs(state: SensorState):
    specs = state['spec_data']
    valid = True
    errors = []
    if specs.get('temp_range', 0) > 500:
        valid = False
        errors.append('Exceeds safe thermal threshold')
    return {'validation_result': valid, 'error_log': errors}

graph = StateGraph(SensorState)
graph.add_node('validate', validate_thermal_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()