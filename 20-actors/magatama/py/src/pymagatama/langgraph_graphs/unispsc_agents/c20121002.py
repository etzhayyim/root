from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    bearing_id: str
    specs: dict
    validation_log: List[str]
    is_approved: bool

def validate_load_capacity(state: BearingState) -> BearingState:
    load = state['specs'].get('load_capacity_rating', 0)
    state['validation_log'].append(f'Validating load: {load}')
    state['is_approved'] = load > 0
    return state

def check_certification(state: BearingState) -> BearingState:
    cert = state['specs'].get('iso_certification_standard')
    if cert:
        state['validation_log'].append(f'ISO standard confirmed: {cert}')
    else:
        state['is_approved'] = False
    return state

builder = StateGraph(BearingState)
builder.add_node('load_check', validate_load_capacity)
builder.add_node('cert_check', check_certification)
builder.add_edge('load_check', 'cert_check')
builder.add_edge('cert_check', END)
builder.set_entry_point('load_check')
graph = builder.compile()