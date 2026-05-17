from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    compliance_cleared: bool
    shipping_reqs: dict

def validate_quality(state: ProcurementState):
    if state['purity_level'] < 99.0:
        raise ValueError('Purity below pharmaceutical standards')
    return {'compliance_cleared': True}

def check_hazmat(state: ProcurementState):
    return {'shipping_reqs': {'type': 'pharmaceutical_hazardous', 'temp': '2-8C'}}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_quality)
builder.add_node('hazmat', check_hazmat)
builder.set_entry_point('validate')
builder.add_edge('validate', 'hazmat')
builder.add_edge('hazmat', END)
graph = builder.compile()