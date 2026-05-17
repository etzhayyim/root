from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OilMonitorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    status: str

def validate_sensor_specs(state: OilMonitorState):
    errors = []
    if state['spec_data'].get('accuracy_ppm', 0) > 5:
        errors.append('Accuracy threshold exceeded')
    return {'validation_errors': errors}

def update_status(state: OilMonitorState):
    return {'status': 'Validated' if not state['validation_errors'] else 'Failed'}

graph = StateGraph(OilMonitorState)
graph.add_node('validate', validate_sensor_specs)
graph.add_node('status', update_status)
graph.add_edge('validate', 'status')
graph.add_edge('status', END)
graph.set_entry_point('validate')
graph = graph.compile()