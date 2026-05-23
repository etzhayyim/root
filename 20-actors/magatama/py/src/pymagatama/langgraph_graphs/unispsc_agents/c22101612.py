from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: RobotState):
    """Validate cleanroom and precision requirements."""
    req = state['specs']
    passed = req.get('iso_rating') <= 5 and req.get('accuracy') < 10
    return {'validation_passed': passed}

def generate_compliance(state: RobotState):
    """Generate automated compliance documentation."""
    return {'compliance_report': 'Compliant for semiconductor industry use.' if state['validation_passed'] else 'Non-compliant'}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
