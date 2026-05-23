from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    drug_name: str
    batch_id: str
    gmp_verified: bool
    compliance_check: bool

def validate_compliance(state: DrugProcurementState):
    state['compliance_check'] = state['gmp_verified'] is True
    return state

def check_batch(state: DrugProcurementState):
    if state['compliance_check']:
        return 'process_order'
    return 'reject'

graph = StateGraph(DrugProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_batch, {'process_order': END, 'reject': END})
