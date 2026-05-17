from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SeedingProcurementState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: SeedingProcurementState):
    errors = []
    if state['specs'].get('hopper_capacity_liters', 0) <= 0:
        errors.append('Invalid hopper capacity')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

builder = StateGraph(SeedingProcurementState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()