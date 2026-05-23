from typing import TypedDict
from langgraph.graph import StateGraph, END

class StylusState(TypedDict):
    model: str
    pressure_supported: bool
    is_compatible: bool

def validate_specs(state: StylusState):
    state['pressure_supported'] = True if 'pressure' in state['model'].lower() else False
    return state

def check_compatibility(state: StylusState):
    state['is_compatible'] = True
    return state

graph = StateGraph(StylusState)
graph.add_node('validate', validate_specs)
graph.add_node('compatible', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatible')
graph.add_edge('compatible', END)
graph = graph.compile()
