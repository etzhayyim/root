from typing import TypedDict
from langgraph.graph import StateGraph, END

class SocketScrewState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: SocketScrewState):
    required = ['material_grade', 'thread_type']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def finalize_procurement(state: SocketScrewState):
    return {**state}

builder = StateGraph(SocketScrewState)
builder.add_node('validate', validate_specs)
builder.add_node('finish', finalize_procurement)
builder.set_entry_point('validate')
builder.add_edge('validate', 'finish')
builder.add_edge('finish', END)
graph = builder.compile()