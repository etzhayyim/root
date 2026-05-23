from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WoundProductState(TypedDict):
    product_name: str
    regulatory_docs: List[str]
    is_compliant: bool

def validate_medical_compliance(state: WoundProductState):
    required_docs = {'ISO_13485', 'Sterilization_Cert'}
    has_docs = all(doc in state['regulatory_docs'] for doc in required_docs)
    return {'is_compliant': has_docs}

def route_by_compliance(state: WoundProductState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(WoundProductState)
graph.add_node('validate', validate_medical_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
