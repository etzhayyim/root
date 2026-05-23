from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class VetEquipmentState(TypedDict):
    equipment_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: VetEquipmentState):
    state['is_approved'] = 'ISO 13485' in state['compliance_docs']
    return state

def route_by_approval(state: VetEquipmentState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(VetEquipmentState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_approval, {'approved': END, 'rejected': END})
graph.compile()
