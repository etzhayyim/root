from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalSetState(TypedDict):
    instrument_list: List[str]
    sterilization_status: str
    compliance_validated: bool

def validate_inventory(state: SurgicalSetState):
    # Business logic for instrument completeness
    return {'compliance_validated': len(state['instrument_list']) > 0}

def perform_quality_check(state: SurgicalSetState):
    # Business logic for sterilization compliance
    return {'sterilization_status': 'COMPLIANT'}

builder = StateGraph(SurgicalSetState)
builder.add_node('inventory', validate_inventory)
builder.add_node('quality', perform_quality_check)
builder.add_edge('inventory', 'quality')
builder.add_edge('quality', END)
builder.set_entry_point('inventory')
graph = builder.compile()