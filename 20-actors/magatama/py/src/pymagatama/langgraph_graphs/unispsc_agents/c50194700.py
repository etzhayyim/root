from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    quality_docs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    # Business logic for puree validation
    brix = state['quality_docs'].get('brix', 0)
    state['approved'] = 10 <= brix <= 20
    return state

def process_logistics(state: ProcurementState):
    print(f'Logistics routing for: {state["product_name"]}')
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_specs)
builder.add_node('logistics', process_logistics)
builder.set_entry_point('validate')
builder.add_edge('validate', 'logistics')
builder.add_edge('logistics', END)
graph = builder.compile()