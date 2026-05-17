from typing import TypedDict
from langgraph.graph import StateGraph, END

class BilliardState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: BilliardState):
    diameter = state['specs'].get('diameter', 0)
    weight = state['specs'].get('weight', 0)
    state['approved'] = (57.15 <= diameter <= 57.25) and (160 <= weight <= 170)
    return state

graph = StateGraph(BilliardState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()