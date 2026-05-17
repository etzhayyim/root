from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    compliance_docs: list
    inspection_result: str

def validate_batch(state: PharmState):
    if state['purity'] >= 99.0:
        return {'inspection_result': 'pass_qc'}
    return {'inspection_result': 'fail_qc'}

def verify_compliance(state: PharmState):
    if len(state['compliance_docs']) >= 3:
        return {'inspection_result': 'cleared_for_release'}
    return {'inspection_result': 'document_pending'}

graph = StateGraph(PharmState)
graph.add_node('qc_check', validate_batch)
graph.add_node('doc_check', verify_compliance)
graph.set_entry_point('qc_check')
graph.add_edge('qc_check', 'doc_check')
graph.add_edge('doc_check', END)
graph = graph.compile()