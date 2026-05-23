from typing import TypedDict
from langgraph.graph import StateGraph, END

class CartState(TypedDict):
    load_capacity: float
    wheel_spec: str
    is_compliant: bool

def validate_specs(state: CartState):
    state['is_compliant'] = state['load_capacity'] > 0 and state['wheel_spec'] != ''
    return state

graph = StateGraph(CartState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
