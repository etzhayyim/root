from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    # Logic to verify medical equipment standard specs
    state['approved'] = 'Height adjustability range' in state['specs']
    return {'approved': state['approved']}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
