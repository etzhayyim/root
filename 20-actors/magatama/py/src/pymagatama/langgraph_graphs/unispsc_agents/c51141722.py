from typing import TypedDict
from langgraph.graph import StateGraph

class DrugProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_status: bool
    approved: bool

def validate_quality(state: DrugProcurementState):
    state['approved'] = state['purity_level'] >= 99.5 and state['gmp_status']
    return state

builder = StateGraph(DrugProcurementState)
builder.add_node('validate', validate_quality)
builder.set_entry_point('validate')
builder.set_finish_point('validate')
graph = builder.compile()