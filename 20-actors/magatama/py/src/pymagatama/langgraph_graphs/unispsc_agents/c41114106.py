from typing import TypedDict
from langgraph.graph import StateGraph, END

class SeismicState(TypedDict):
    specs: dict
    validation_status: str
    compliance_risk: bool

def validate_specs(state: SeismicState):
    s = state['specs']
    valid = all(key in s for key in ['sampling_rate_hz', 'dynamic_range_db'])
    return {'validation_status': 'passed' if valid else 'rejected'}

def check_compliance(state: SeismicState):
    risk = state['specs'].get('frequency_response_range', 0) > 100
    return {'compliance_risk': risk}

graph = StateGraph(SeismicState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
