from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    temp_log: list
    compliance_cleared: bool

def validate_cold_chain(state: ProcurementState):
    if all(2 <= temp <= 8 for temp in state['temp_log']):
        return {'compliance_cleared': True}
    return {'compliance_cleared': False}

def finalize_order(state: ProcurementState):
    return {'status': 'READY_FOR_SHIPMENT' if state['compliance_cleared'] else 'REJECTED'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
