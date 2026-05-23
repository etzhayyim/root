from typing import TypedDict
from langgraph.graph import StateGraph, END

class CrucibleState(TypedDict):
    material_spec: str
    temp_rating: float
    validation_passed: bool

def validate_specs(state: CrucibleState):
    state['validation_passed'] = state['temp_rating'] >= 1500
    return state

graph = StateGraph(CrucibleState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
