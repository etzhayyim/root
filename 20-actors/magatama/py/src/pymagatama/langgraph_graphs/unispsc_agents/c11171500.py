from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PreciousMetalState(TypedDict):
    commodity_code: str
    purity_check: bool
    export_license_required: bool
    validation_log: List[str]

def validate_purity(state: PreciousMetalState):
    # Simulate purity check logic
    state['purity_check'] = True
    state['validation_log'].append('Purity validated to 99.99%')
    return state

def check_export_controls(state: PreciousMetalState):
    # Simulate dual-use check
    state['export_license_required'] = True
    state['validation_log'].append('Export license flagged for dual-use review')
    return state

def finalize_procurement(state: PreciousMetalState):
    state['validation_log'].append('Procurement workflow finalized')
    return state

builder = StateGraph(PreciousMetalState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_export', check_export_controls)
builder.add_node('finalize', finalize_procurement)
builder.add_edge('validate_purity', 'check_export')
builder.add_edge('check_export', 'finalize')
builder.add_edge('finalize', END)
builder.set_entry_point('validate_purity')
graph = builder.compile()