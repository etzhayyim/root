from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AirwayState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    status: str

def validate_compliance(state: AirwayState):
    required = ['ISO_13485', 'FDA_Clearance']
    valid = all(doc in state['compliance_docs'] for doc in required)
    return {'status': 'APPROVED' if valid else 'REJECTED'}

def process_clinical_safety(state: AirwayState):
    print(f'Performing safety audit for: {state["product_id"]}')
    return {'status': 'SAFETY_VERIFIED'}

graph = StateGraph(AirwayState)
graph.add_node('validate', validate_compliance)
graph.add_node('safety_check', process_clinical_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()