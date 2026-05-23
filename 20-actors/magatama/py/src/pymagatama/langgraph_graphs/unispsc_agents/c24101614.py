from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirbagState(TypedDict):
    pressure_rating: float
    material_certified: bool
    validation_passed: bool

def validate_specs(state: AirbagState):
    state['validation_passed'] = state['pressure_rating'] > 0 and state['material_certified'] is True
    return state

graph_builder = StateGraph(AirbagState)
graph_builder.add_node('validate', validate_specs)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()
