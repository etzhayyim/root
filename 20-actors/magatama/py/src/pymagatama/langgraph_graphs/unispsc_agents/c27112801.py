from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrillBitState(TypedDict):
    specification: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: DrillBitState):
    required = ['material', 'diameter', 'shank_type']
    passed = all(k in state['specification'] for k in required)
    return {'validation_passed': passed}

def generate_compliance(state: DrillBitState):
    return {'compliance_report': 'Standard compliant' if state['validation_passed'] else 'Invalid'}

graph = StateGraph(DrillBitState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()