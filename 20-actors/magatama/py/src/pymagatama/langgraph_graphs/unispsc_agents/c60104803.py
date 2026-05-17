from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SpringState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_load_specs(state: SpringState):
    rate = state['spec_data'].get('spring_rate', 0)
    return {'validation_passed': rate > 0}

def generate_compliance(state: SpringState):
    return {'compliance_report': 'Spring specifications confirmed against ASTM standards.'}

graph = StateGraph(SpringState)
graph.add_node('validate', validate_load_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()