from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class SoftwareProcurementState(TypedDict):
    license_key: str
    compatibility_report: list[str]
    approved: bool

def validate_license(state: SoftwareProcurementState) -> SoftwareProcurementState:
    # Logic for validating license keys
    state['approved'] = len(state['license_key']) > 10
    return state

def check_compatibility(state: SoftwareProcurementState) -> SoftwareProcurementState:
    # Logic for compatibility check
    state['compatibility_report'] = ['OS_SUPPORTED', 'RAM_OPTIMIZED']
    return state

builder = StateGraph(SoftwareProcurementState)
builder.add_node('validate', validate_license)
builder.add_node('compatibility', check_compatibility)
builder.add_edge('validate', 'compatibility')
builder.add_edge('compatibility', END)
builder.set_entry_point('validate')
graph = builder.compile()
