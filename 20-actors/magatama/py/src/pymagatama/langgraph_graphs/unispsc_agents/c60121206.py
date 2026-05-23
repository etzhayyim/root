from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PaintProcurementState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_safety_certs(state: PaintProcurementState):
    required = {'toxicology_report', 'dermatological_test'}
    state['is_approved'] = required.issubset(set(state['compliance_docs']))
    return state

graph = StateGraph(PaintProcurementState)
graph.add_node('validate', validate_safety_certs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
