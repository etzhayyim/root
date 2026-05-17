from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    specs: dict
    validation_status: bool

def validate_specs(state: FurnaceState):
    required = ['temperature_range', 'protocol']
    return {'validation_status': all(k in state['specs'] for k in required)}

def compile_graph():
    graph = StateGraph(FurnaceState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = compile_graph()