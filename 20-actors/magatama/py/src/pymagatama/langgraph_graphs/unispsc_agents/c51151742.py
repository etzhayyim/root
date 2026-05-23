from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_verified: bool

def validate_quality(state: ProcurementState):
    print(f'Validating batch {state["batch_id"]}')
    return {'compliance_verified': state['purity_level'] >= 99.0}

def update_records(state: ProcurementState):
    print('Updating procurement database')
    return {}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_quality)
builder.add_node('record', update_records)
builder.set_entry_point('validate')
builder.add_edge('validate', 'record')
builder.add_edge('record', END)
graph = builder.compile()
