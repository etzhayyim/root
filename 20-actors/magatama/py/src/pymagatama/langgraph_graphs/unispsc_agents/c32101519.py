from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DetectorState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_sensor_specs(state: DetectorState):
    required = ['detection_range', 'response_time_ms']
    errors = []
    for field in required:
        if field not in state['specs']:
            errors.append(f'Missing {field}')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_by_validation(state: DetectorState):
    return 'process' if state['validation_passed'] else 'flag_error'

graph = StateGraph(DetectorState)
graph.add_node('validate', validate_sensor_specs)
graph.add_node('process', lambda x: {'errors': []})
graph.add_node('flag_error', lambda x: {'errors': ['Critical Spec Missing']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph.add_edge('flag_error', END)
graph = graph.compile()