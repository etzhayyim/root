from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    quality_docs: List[str]
    is_approved: bool

def validate_food_standards(state: ProcurementState):
    # Business logic for prune quality inspection
    state['is_approved'] = 'pesticide_check' in state['quality_docs']
    return state

def check_storage_requirements(state: ProcurementState):
    print('Verifying cold chain logistics for prunes')
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_food_standards)
builder.add_node('storage', check_storage_requirements)
builder.set_entry_point('validate')
builder.add_edge('validate', 'storage')
builder.add_edge('storage', END)
graph = builder.compile()
