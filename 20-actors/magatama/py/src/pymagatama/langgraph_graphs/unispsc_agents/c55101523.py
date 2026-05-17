from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    order_id: str
    spec_data: dict
    validation_result: bool

def validate_notebook_specs(state: ProcurementState):
    specs = state['spec_data']
    required = ['paper_gsm', 'binding_type']
    is_valid = all(k in specs for k in required)
    return {'validation_result': is_valid}

def process_procurement(state: ProcurementState):
    if state['validation_result']:
        print(f'Processing order {state['order_id']} for printing.')
    return {}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_notebook_specs)
builder.add_node('process', process_procurement)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()