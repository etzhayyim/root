from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    chemical_name: str
    compliance_docs: List[str]
    approved: bool

def validate_hazardous_substance(state: ProcurementState):
    required_docs = {'MSDS', 'HazMat_Permit', 'Regulatory_Clearance'}
    has_docs = all(doc in state['compliance_docs'] for doc in required_docs)
    return {'approved': has_docs}

def route_by_compliance(state: ProcurementState):
    return 'approved' if state['approved'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_hazardous_substance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()