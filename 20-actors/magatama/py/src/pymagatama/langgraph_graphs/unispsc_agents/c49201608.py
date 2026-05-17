from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    is_verified: bool

def validate_grip_specs(state: ProcurementState):
    resistance = state['specs'].get('resistance_level_kg', 0)
    state['is_verified'] = resistance > 0 and resistance < 150
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_grip_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()