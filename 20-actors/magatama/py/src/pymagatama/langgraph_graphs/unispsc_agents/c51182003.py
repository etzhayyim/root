from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    compliance_docs: List[str]
    status: str

def validate_pharma_docs(state: ProcurementState):
    required = ['CoA', 'GMP_Certificate']
    valid = all(doc in state['compliance_docs'] for doc in required)
    return {'status': 'validated' if valid else 'rejected'}

def update_inventory(state: ProcurementState):
    return {'status': 'inventory_locked' if state['status'] == 'validated' else 'failed'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pharma_docs)
graph.add_node('inventory', update_inventory)
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph.set_entry_point('validate')
graph = graph.compile()