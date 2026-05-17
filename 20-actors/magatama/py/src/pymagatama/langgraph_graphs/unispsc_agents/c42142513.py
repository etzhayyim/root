from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiologyNeedleState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_status: str

def validate_medical_spec(state: RadiologyNeedleState):
    required_fields = ['gauge', 'material', 'sterilization']
    passed = all(k in state['spec_data'] for k in required_fields)
    return {'validation_passed': passed, 'compliance_status': 'COMPLIANT' if passed else 'INCOMPLETE'}

def check_regulatory(state: RadiologyNeedleState):
    if state['validation_passed']:
        print('Performing regulatory compliance verification...')
        return {'compliance_status': 'APPROVED'}
    return {'compliance_status': 'REJECTED'}

graph = StateGraph(RadiologyNeedleState)
graph.add_node('validate', validate_medical_spec)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()