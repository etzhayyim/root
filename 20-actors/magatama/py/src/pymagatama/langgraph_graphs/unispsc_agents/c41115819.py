from typing import TypedDict
from langgraph.graph import StateGraph, END

class AnalyzerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: AnalyzerState):
    mandatory_fields = ['calibration_cert', 'iso_13485_ref']
    passed = all(field in state['spec_data'] for field in mandatory_fields)
    return {'validation_passed': passed}

def route_verification(state: AnalyzerState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(AnalyzerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
