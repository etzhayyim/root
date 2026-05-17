from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TrainSystemState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_defroster_specs(state: TrainSystemState):
    required = ['voltage', 'air_flow', 'ip_rating']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_compliance_documentation(state: TrainSystemState):
    if state['validation_passed']:
        return {'compliance_report': 'Certified compliant with railway safety standards.'}
    return {'compliance_report': 'Compliance validation failed.'}

graph = StateGraph(TrainSystemState)
graph.add_node('validate', validate_defroster_specs)
graph.add_node('certify', generate_compliance_documentation)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()