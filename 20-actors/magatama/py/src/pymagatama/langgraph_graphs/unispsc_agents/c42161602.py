from typing import TypedDict
from langgraph.graph import StateGraph, END

class DialysisState(TypedDict):
    spec_data: dict
    compliance_passed: bool

def validate_medical_specs(state: DialysisState):
    required = ['sterilization', 'material_grade']
    passed = all(k in state['spec_data'] for k in required)
    return {'compliance_passed': passed}

def process_registration(state: DialysisState):
    print('Registering Hemodialysis sampler...')
    return {'compliance_passed': True}

graph = StateGraph(DialysisState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('register', process_registration)
graph.add_edge('validate', 'register')
graph.add_edge('register', END)
graph.set_entry_point('validate')
graph = graph.compile()