from typing import TypedDict
from langgraph.graph import StateGraph, END

class EKGState(TypedDict):
    device_id: str
    compliance_docs: list[str]
    validation_passed: bool

def validate_medical_cert(state: EKGState):
    state['validation_passed'] = 'FDA_Cert' in state['compliance_docs']
    return state

def check_signal_specs(state: EKGState):
    return state

graph = StateGraph(EKGState)
graph.add_node('validate', validate_medical_cert)
graph.add_node('signal', check_signal_specs)
graph.add_edge('validate', 'signal')
graph.add_edge('signal', END)
graph.set_entry_point('validate')
graph = graph.compile()
