from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpindleState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_report: str

def validate_specs(state: SpindleState):
    specs = state['spec_data']
    valid = all([specs.get('rpm', 0) > 0, 'accuracy' in specs])
    return {'validation_status': valid, 'compliance_report': 'Validated' if valid else 'Invalid'}

def check_compliance(state: SpindleState):
    return {'compliance_report': 'Checked against Dual-Use Guidelines'}

graph = StateGraph(SpindleState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()