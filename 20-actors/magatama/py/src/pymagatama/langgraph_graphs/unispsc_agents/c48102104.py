from typing import TypedDict
from langgraph.graph import StateGraph, END

class DisplayCaseState(TypedDict):
    temp_range: str
    energy_rating: float
    food_safety_cert: bool
    approved: bool

def validate_specs(state: DisplayCaseState):
    is_valid = state['temp_range'] == '-18C to -25C' and state['food_safety_cert']
    return {'approved': is_valid}

graph = StateGraph(DisplayCaseState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
