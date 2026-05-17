from typing import TypedDict
from langgraph.graph import StateGraph, END

class IceChestState(TypedDict):
    capacity_liters: float
    thermal_rating_hours: int
    is_food_grade: bool
    validation_passed: bool

def validate_specs(state: IceChestState):
    passed = state['capacity_liters'] > 0 and state['thermal_rating_hours'] >= 24
    return {'validation_passed': passed}

graph = StateGraph(IceChestState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()