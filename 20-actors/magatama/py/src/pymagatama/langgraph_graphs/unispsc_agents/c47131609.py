from typing import TypedDict
from langgraph.graph import StateGraph, END

class HandleState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: HandleState):
    required = ['material', 'length']
    valid = all(k in state['specs'] for k in required)
    return {'approved': valid}

graph = StateGraph(HandleState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()