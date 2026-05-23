from typing import TypedDict
from langgraph.graph import StateGraph, END

class DeskStorageState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: DeskStorageState):
    required = ['dimensions', 'material']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def route_by_material(state: DeskStorageState):
    return 'process_metal' if state['specs'].get('material') == 'metal' else 'process_generic'

builder = StateGraph(DeskStorageState)
builder.add_node('validate', validate_specs)
builder.add_node('process_metal', lambda x: x)
builder.add_node('process_generic', lambda x: x)
builder.set_entry_point('validate')
builder.add_conditional_edges('validate', route_by_material)
builder.add_edge('process_metal', END)
builder.add_edge('process_generic', END)
graph = builder.compile()
