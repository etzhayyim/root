import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_load_capacity(state: ContainerState):
    capacity = state['specs'].get('load_capacity', 0)
    if capacity <= 0:
        state['validation_errors'].append('Invalid capacity')
        state['is_compliant'] = False
    return state

def check_dimensions(state: ContainerState):
    if not state.get('specs', {}).get('dimensions'):
        state['validation_errors'].append('Missing dimensions')
        state['is_compliant'] = False
    return state

builder = StateGraph(ContainerState)
builder.add_node('load_check', validate_load_capacity)
builder.add_node('dim_check', check_dimensions)
builder.add_edge('load_check', 'dim_check')
builder.add_edge('dim_check', END)
builder.set_entry_point('load_check')
graph = builder.compile()