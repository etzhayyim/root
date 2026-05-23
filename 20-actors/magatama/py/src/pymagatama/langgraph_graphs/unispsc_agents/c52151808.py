from typing import TypedDict
from langgraph.graph import StateGraph, END
class CookerState(TypedDict):
    spec_data: dict
    approved: bool
def validate_safety_mechanisms(state: CookerState):
    pressure_val = state['spec_data'].get('bar', 0)
    state['approved'] = 0.8 <= pressure_val <= 1.2
    return state
graph = StateGraph(CookerState)
graph.add_node('validate', validate_safety_mechanisms)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
