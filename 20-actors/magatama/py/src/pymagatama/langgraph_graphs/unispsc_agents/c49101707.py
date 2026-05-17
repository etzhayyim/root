from typing import TypedDict
from langgraph.graph import StateGraph, END

class CertificateState(TypedDict):
    order_id: str
    validation_passed: bool
    security_features: list
    final_proof: str

def validate_specs(state: CertificateState):
    # Simulate CAD/Spec validation for document aesthetics
    state['validation_passed'] = all(f in state['security_features'] for f in ['embossing', 'hologram'])
    print(f'Validating order {state['order_id']}: {state['validation_passed']}')
    return state

def approve_proof(state: CertificateState):
    state['final_proof'] = 'APPROVED_V1'
    return state

graph = StateGraph(CertificateState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_proof)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()