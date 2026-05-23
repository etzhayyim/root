from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DebridementState(TypedDict):
    product_id: str
    compliance_status: bool
    sterility_check: bool

def validate_compliance(state: DebridementState):
    state['compliance_status'] = True
    return 'compliance_verified'

def check_sterility(state: DebridementState):
    state['sterility_check'] = True
    return 'sterility_verified'

builder = StateGraph(DebridementState)
builder.add_node('compliance', validate_compliance)
builder.add_node('sterility', check_sterility)
builder.add_edge('compliance', 'sterility')
builder.set_entry_point('compliance')
builder.add_edge('sterility', END)
graph = builder.compile()
