from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class AnalyzerState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_flag: bool
def validate_specs(state: AnalyzerState):
    required_keys = ['frequency_range', 'calibration_cert']
    valid = all(k in state['spec_data'] for k in required_keys)
    return {'validation_passed': valid}
def check_compliance(state: AnalyzerState):
    is_dual = state['spec_data'].get('frequency_range', 0) > 3e9
    return {'export_flag': is_dual}
graph = StateGraph(AnalyzerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
