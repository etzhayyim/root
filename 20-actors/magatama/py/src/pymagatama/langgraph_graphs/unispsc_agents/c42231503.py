from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    status: str

def validate_medical_docs(state: ProcurementState):
    required = ['ISO10993', 'SterilizationCert']
    valid = all(doc in state['compliance_docs'] for doc in required)
    return {'status': 'APPROVED' if valid else 'REJECTED'}

def route_by_compliance(state: ProcurementState):
    return 'validate' if state['status'] == 'PENDING' else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_docs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
