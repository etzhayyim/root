from typing import TypedDict
from langgraph.graph import StateGraph, END

class RiserState(TypedDict):
    capacity_kg: float
    adjustment_range_mm: float
    is_compliant: bool

def validate_specs(state: RiserState):
    state['is_compliant'] = state['capacity_kg'] >= 10.0 and state['adjustment_range_mm'] >= 300
    return state

graph = StateGraph(RiserState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()