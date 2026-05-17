from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserProcurementState(TypedDict):
    laser_class: str
    power_rating: float
    compliance_docs: bool
    approved: bool

def validate_safety(state: LaserProcurementState):
    state['approved'] = state['laser_class'] in ['Class 4'] and state['compliance_docs']
    return state

builder = StateGraph(LaserProcurementState)
builder.add_node('validate', validate_safety)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()