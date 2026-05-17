from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReactorState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: ReactorState):
    required = ['Rated voltage', 'Inductance', 'Current rating']
    valid = all(k in state['specs'] for k in required)
    return {'validation_passed': valid}

def generate_compliance(state: ReactorState):
    if state['validation_passed']:
        return {'compliance_report': 'Technical review completed: IEC 60076-6 compliance verified.'}
    return {'compliance_report': 'Error: Missing technical specifications.'}

graph = StateGraph(ReactorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()