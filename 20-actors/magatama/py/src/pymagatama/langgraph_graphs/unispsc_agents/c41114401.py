from typing import TypedDict
from langgraph.graph import StateGraph, END
class AnemometerState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list
def validate_specs(state: AnemometerState):
    required = ['measurement_range_m_s', 'calibration_certificate']
    errors = [f for f in required if f not in state['spec_data']]
    return {'validation_result': len(errors) == 0, 'error_log': [f'Missing: {e}' for e in errors]}
def route_by_validation(state: AnemometerState):
    return 'valid' if state['validation_result'] else 'invalid'
graph = StateGraph(AnemometerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()