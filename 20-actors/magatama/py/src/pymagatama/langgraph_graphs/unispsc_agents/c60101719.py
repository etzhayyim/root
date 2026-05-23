from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PocketChartState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: PocketChartState):
    errors = []
    if state['spec_data'].get('width', 0) <= 0:
        errors.append('Invalid width')
    return {'validation_errors': errors}

def approve_procurement(state: PocketChartState):
    return {'is_approved': len(state['validation_errors']) == 0}

builder = StateGraph(PocketChartState)
builder.add_node('validate', validate_dimensions)
builder.add_node('approve', approve_procurement)
builder.add_edge('validate', 'approve')
builder.add_edge('approve', END)
builder.set_entry_point('validate')
graph = builder.compile()
