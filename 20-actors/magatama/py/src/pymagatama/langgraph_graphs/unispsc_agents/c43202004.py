from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiskState(TypedDict):
    quantity: int
    format: str
    is_verified: bool

def validate_format(state: DiskState):
    valid_formats = ['3.5-inch-HD', '5.25-inch-DD']
    return {'is_verified': state['format'] in valid_formats}

def finalize_order(state: DiskState):
    return {'is_verified': True}

graph = StateGraph(DiskState)
graph.add_node('validate', validate_format)
graph.add_node('finish', finalize_order)
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph.set_entry_point('validate')
app = graph.compile()