from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MagnesiumForgingState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: MagnesiumForgingState):
    required_keys = ['material_grade', 'tolerance', 'ndt_results']
    passed = all(k in state['specs'] for k in required_keys)
    return {'validation_passed': passed, 'compliance_report': 'Success' if passed else 'Missing Specs'}

def conduct_risk_assessment(state: MagnesiumForgingState):
    risk = 'Low' if state['validation_passed'] else 'High'
    return {'compliance_report': f'Risk assessment completed: {risk}'}

graph = StateGraph(MagnesiumForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('risk', conduct_risk_assessment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk')
graph.add_edge('risk', END)
graph = graph.compile()
