from langgraph.graph import StateGraph, END
from typing import TypedDict
class RadarSpecState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list
def validate_frequency(state: RadarSpecState):
    bands = state['spec_data'].get('bands', [])
    valid = all(isinstance(b, (int, float)) for b in bands)
    return {'validation_result': valid, 'error_log': [] if valid else ['Invalid frequency format']}
def compliance_check(state: RadarSpecState):
    is_certified = state['spec_data'].get('certified', False)
    return {'validation_result': state['validation_result'] and is_certified}
graph = StateGraph(RadarSpecState)
graph.add_node('validate_freq', validate_frequency)
graph.add_node('compliance', compliance_check)
graph.add_edge('validate_freq', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate_freq')
graph = graph.compile()