from typing import TypedDict
from langgraph.graph import StateGraph, END

class BladeState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: BladeState):
    required = ['TPI', 'Material']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

graph = StateGraph(BladeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
