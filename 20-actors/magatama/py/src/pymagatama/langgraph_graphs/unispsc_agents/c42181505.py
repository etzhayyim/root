from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    validation_status: bool

def validate_medical_device(state: ProcurementState):
    # Business logic for endometrial sampler compliance
    docs = state.get('compliance_docs', [])
    is_valid = 'ISO13485' in docs and 'Sterilization_Cert' in docs
    return {'validation_status': is_valid}

def process_shipment(state: ProcurementState):
    print(f'Processing medical device batch: {state['item_id']}')
    return {'validation_status': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate_compliance', validate_medical_device)
graph.add_node('mark_ready', process_shipment)
graph.add_edge('validate_compliance', 'mark_ready')
graph.add_edge('mark_ready', END)
graph.set_entry_point('validate_compliance')
graph = graph.compile()