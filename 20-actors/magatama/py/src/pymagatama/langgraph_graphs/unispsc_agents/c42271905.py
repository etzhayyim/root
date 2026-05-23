from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MedicalSupplyState(TypedDict):
    supply_id: str
    compliance_docs: List[str]
    is_cleared: bool

def validate_compliance(state: MedicalSupplyState):
    required = ['ISO_13485', 'CE_MARKING', 'STERILITY_REPORT']
    is_cleared = all(doc in state['compliance_docs'] for doc in required)
    return {'is_cleared': is_cleared}

def route_by_compliance(state: MedicalSupplyState):
    return 'approved' if state['is_cleared'] else 'rejected'

graph = StateGraph(MedicalSupplyState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph.compile()
