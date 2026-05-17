from typing import TypedDict
from langgraph.graph import StateGraph, END

class CheeseProcurementState(TypedDict):
    batch_id: str
    temp_check: bool
    sanitation_ok: bool
    approved: bool

def validate_temp(state: CheeseProcurementState):
    # Simulate monitoring of cold chain
    print(f'Validating storage for {state['batch_id']}')
    return {'temp_check': True}

def check_compliance(state: CheeseProcurementState):
    # Verify HACCP documentation
    return {'sanitation_ok': True, 'approved': True}

builder = StateGraph(CheeseProcurementState)
builder.add_node('validate_storage', validate_temp)
builder.add_node('compliance_review', check_compliance)
builder.add_edge('validate_storage', 'compliance_review')
builder.add_edge('compliance_review', END)
builder.set_entry_point('validate_storage')
graph = builder.compile()