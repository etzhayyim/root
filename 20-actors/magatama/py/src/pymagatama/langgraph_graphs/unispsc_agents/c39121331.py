from typing import TypedDict
from langgraph.graph import StateGraph, END

class HazardBoxState(TypedDict):
    specs: dict
    approved: bool
    compliance_report: str

def validate_compliance(state: HazardBoxState):
    required = ['ATEX_Certification', 'IP_Rating']
    valid = all(k in state['specs'] for k in required)
    return {'approved': valid, 'compliance_report': 'Verified' if valid else 'Missing certs'}

def finalize_order(state: HazardBoxState):
    return {'compliance_report': f'Finalized: {state['compliance_report']}'}

graph = StateGraph(HazardBoxState)
graph.add_node('validate', validate_compliance)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
