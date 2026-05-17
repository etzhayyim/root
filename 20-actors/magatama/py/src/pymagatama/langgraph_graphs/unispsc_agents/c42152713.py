from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrthoToolState(TypedDict):
    specs: dict
    validated: bool
    compliance_score: float

def validate_specs(state: OrthoToolState):
    # Simulate validation logic for medical device specs
    required = ['ISO 13485', 'Material_Cert']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: OrthoToolState):
    state['compliance_score'] = 1.0 if state['validated'] else 0.0
    return state

graph = StateGraph(OrthoToolState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()