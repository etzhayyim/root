from typing import TypedDict
from langgraph.graph import StateGraph, END

class BiotechSpecState(TypedDict):
    material_name: str
    purity_level: float
    requires_cold_chain: bool
    validation_status: str

def validate_purity(state: BiotechSpecState):
    if state['purity_level'] < 0.99:
        return {'validation_status': 'REJECTED_LOW_PURITY'}
    return {'validation_status': 'PASSED_QUALITY_CHECK'}

def process_logistics(state: BiotechSpecState):
    if state['requires_cold_chain']:
        return {'validation_status': 'LOGISTICS_PENDING_TEMP_CONTROL'}
    return {'validation_status': 'READY_FOR_SHIPMENT'}

graph = StateGraph(BiotechSpecState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', process_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()