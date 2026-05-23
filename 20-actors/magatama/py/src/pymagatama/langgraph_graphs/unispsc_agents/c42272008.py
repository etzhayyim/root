from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class IntubationState(TypedDict):
    compliance_docs: List[str]
    certification_valid: bool
    inspection_passed: bool
def validate_medical_docs(state: IntubationState):
    state['certification_valid'] = all(doc in state['compliance_docs'] for doc in ['ISO_13485', 'CE_Mark'])
    return state
def run_qc(state: IntubationState):
    state['inspection_passed'] = state['certification_valid']
    return state
graph = StateGraph(IntubationState)
graph.add_node('validate', validate_medical_docs)
graph.add_node('qc', run_qc)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()
