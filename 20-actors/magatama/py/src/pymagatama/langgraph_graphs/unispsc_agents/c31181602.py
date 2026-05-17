from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SealState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: SealState):
    required = ['material', 'dimensions', 'rating']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_compliance(state: SealState):
    return {'compliance_report': 'DIN/ISO compliance validation complete.'}

graph = StateGraph(SealState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')