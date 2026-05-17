from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CertificateState(TypedDict):
    data: dict
    validation_passed: bool
    errors: List[str]

def validate_security_features(state: CertificateState):
    features = state['data'].get('security_features', [])
    passed = 'watermark' in features and 'hologram' in features
    return {'validation_passed': passed, 'errors': [] if passed else ['Missing mandatory security features']}

def finalize_document(state: CertificateState):
    return {'data': {**state['data'], 'status': 'READY_FOR_PRINT'}}

graph = StateGraph(CertificateState)
graph.add_node('validate', validate_security_features)
graph.add_node('finalize', finalize_document)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()