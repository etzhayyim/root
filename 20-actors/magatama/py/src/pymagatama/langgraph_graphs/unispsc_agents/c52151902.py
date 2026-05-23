from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BakingPanState(TypedDict):
    material: str
    max_temp: int
    is_food_safe: bool
    validation_passed: bool

def validate_specs(state: BakingPanState):
    state['validation_passed'] = state['is_food_safe'] and state['max_temp'] >= 220
    return state

graph = StateGraph(BakingPanState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
