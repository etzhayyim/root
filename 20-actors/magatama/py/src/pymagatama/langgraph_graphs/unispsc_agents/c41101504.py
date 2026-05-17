from typing import TypedDict
from langgraph.graph import StateGraph, END

class HomogenizerState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: HomogenizerState):
    if state['specs'].get('power_rating', 0) > 0:
        return {'validation_passed': True, 'compliance_risk': 'low'}
    return {'validation_passed': False, 'compliance_risk': 'high'}

def check_compliance(state: HomogenizerState):
    return {'compliance_risk': 'reviewed'}

graph = StateGraph(HomogenizerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()