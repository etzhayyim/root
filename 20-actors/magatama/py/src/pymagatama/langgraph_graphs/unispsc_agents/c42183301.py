from typing import TypedDict
from langgraph.graph import StateGraph, END

class ENTProcurementState(TypedDict):
    product_id: str
    compliance_docs: list
    validation_status: bool

def validate_medical_cert(state: ENTProcurementState):
    # Simulate validation of ISO 13485 docs
    state['validation_status'] = len(state['compliance_docs']) > 0
    return state

def route_by_validation(state: ENTProcurementState):
    return 'process' if state['validation_status'] else END

graph = StateGraph(ENTProcurementState)
graph.add_node('validate', validate_medical_cert)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
