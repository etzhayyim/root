from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    compliance_report: str
    is_approved: bool

def validate_compliance(state: LightingState):
    required = ['UL924', 'IP_Rating']
    valid = all(k in state['spec_data'] for k in required)
    return {'compliance_report': 'Passed' if valid else 'Failed', 'is_approved': valid}

def finalize_order(state: LightingState):
    return {'compliance_report': 'Order Queued for Procurement'}

builder = StateGraph(LightingState)
builder.add_node('validate', validate_compliance)
builder.add_node('final', finalize_order)
builder.add_edge('validate', 'final')
builder.set_entry_point('validate')
builder.add_edge('final', END)
graph = builder.compile()
