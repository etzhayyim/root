from typing import TypedDict
from langgraph.graph import StateGraph, END

class FrameState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: FrameState):
    required = ['Material', 'Dimensions']
    return {'validated': all(k in state['specs'] for k in required)}

graph = StateGraph(FrameState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()