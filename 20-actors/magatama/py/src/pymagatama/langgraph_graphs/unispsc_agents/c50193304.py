from typing import TypedDict
from langgraph.graph import StateGraph, END

class LemonProcessState(TypedDict):
    batch_id: str
    quality_status: str
    compliance_checked: bool

def validate_batch(state: LemonProcessState):
    print(f'Validating batch {state['batch_id']}')
    return {'quality_status': 'verified', 'compliance_checked': True}

def approve_shipment(state: LemonProcessState):
    print('Approving shipment for food production usage')
    return {'quality_status': 'approved'}

graph = StateGraph(LemonProcessState)
graph.add_node('validate', validate_batch)
graph.add_node('approve', approve_shipment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()
