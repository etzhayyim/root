from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_temp_specs(state: ContainerState):
    required = ['R-value', 'duration']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_compliance(state: ContainerState):
    return {'compliance_report': 'Validated against GDP standards' if state['validation_passed'] else 'Failed'}

graph = StateGraph(ContainerState)
graph.add_node('validate', validate_temp_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()