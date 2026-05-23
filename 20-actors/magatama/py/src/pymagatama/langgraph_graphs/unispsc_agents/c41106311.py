from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RNAProcurementState(TypedDict):
    spec_requirements: dict
    validation_status: str
    shipping_conditions: str

def validate_purity(state: RNAProcurementState):
    purity = state['spec_requirements'].get('purity_ratio', 0)
    status = 'APPROVED' if 1.8 <= purity <= 2.2 else 'REJECTED'
    return {'validation_status': status}

def check_temp(state: RNAProcurementState):
    temp = state['spec_requirements'].get('storage_temperature', 0)
    shipping = 'COLD_CHAIN_REQUIRED' if temp <= -20 else 'DRY_ICE_REQUIRED'
    return {'shipping_conditions': shipping}

graph = StateGraph(RNAProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('shipping', check_temp)
graph.set_entry_point('validate')
graph.add_edge('validate', 'shipping')
graph.add_edge('shipping', END)
graph = graph.compile()
