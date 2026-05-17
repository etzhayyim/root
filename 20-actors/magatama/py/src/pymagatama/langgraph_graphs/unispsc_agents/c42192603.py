from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    approved: bool

def validate_medical_safety(state: ProcurementState):
    # Simulate validation of medical safety standards
    state['approved'] = all(['ISO_13485' in doc or 'FDA_Class_I' in doc for doc in state['compliance_docs']])
    return state

def route_by_approval(state: ProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

app = graph.compile()