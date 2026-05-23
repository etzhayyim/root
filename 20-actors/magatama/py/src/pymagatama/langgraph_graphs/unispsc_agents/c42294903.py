from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NeedleProcurementState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: NeedleProcurementState):
    required = ['ISO_13485', 'Sterilization_Cert']
    state['is_approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

graph = StateGraph(NeedleProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
