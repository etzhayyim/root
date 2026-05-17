from typing import TypedDict
from langgraph.graph import StateGraph, END

class MountingSpecState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_load_capacity(state: MountingSpecState) -> MountingSpecState:
    load = state['spec_data'].get('load_capacity', 0)
    if load <= 0:
        state['error_log'].append('Invalid load capacity')
        state['validated'] = False
    return state

def check_material_specs(state: MountingSpecState) -> MountingSpecState:
    if 'material' not in state['spec_data']:
        state['error_log'].append('Material missing')
        state['validated'] = False
    return state

builder = StateGraph(MountingSpecState)
builder.add_node('load_check', validate_load_capacity)
builder.add_node('material_check', check_material_specs)
builder.set_entry_point('load_check')
builder.add_edge('load_check', 'material_check')
builder.add_edge('material_check', END)
graph = builder.compile()