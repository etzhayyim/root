from typing import TypedDict
from langgraph.graph import StateGraph, END

class PotProcurementState(TypedDict):
    material: str
    capacity_l: float
    food_safety_cleared: bool

def validate_specs(state: PotProcurementState):
    if state['capacity_l'] <= 0:
        raise ValueError('Capacity must be positive')
    return {'food_safety_cleared': True}

graph = StateGraph(PotProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()