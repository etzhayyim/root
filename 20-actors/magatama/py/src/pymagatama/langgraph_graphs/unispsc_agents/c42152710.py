from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OrthoState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_biocompatibility(state: OrthoState):
    # Simulate check for ISO 10993 compliance
    state['is_approved'] = 'ISO_10993' in state['compliance_docs']
    return 'check_qc'

def check_qc(state: OrthoState):
    return 'end_node'

graph = StateGraph(OrthoState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('check_qc', check_qc)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_qc')
graph.add_edge('check_qc', END)
graph = graph.compile()
