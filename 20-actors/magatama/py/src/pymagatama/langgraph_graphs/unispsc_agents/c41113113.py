from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasAnalyzerState(TypedDict):
    analyzer_data: dict
    validation_passed: bool
    compliance_status: str

def validate_specs(state: GasAnalyzerState):
    data = state.get('analyzer_data', {})
    required = ['range', 'calibration_cert']
    passed = all(k in data for k in required)
    return {'validation_passed': passed, 'compliance_status': 'COMPLIANT' if passed else 'PENDING'}

def check_compliance(state: GasAnalyzerState):
    return 'END'

graph = StateGraph(GasAnalyzerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()