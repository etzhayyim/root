from typing import TypedDict
from langgraph.graph import StateGraph, END

class BicycleState(TypedDict):
    frame_material: str
    brake_system: str
    is_compliant: bool

def validate_specs(state: BicycleState):
    state['is_compliant'] = state['frame_material'] in ['Aluminum', 'Steel', 'Carbon Fiber'] and state['brake_system'] == 'Disc'
    return state

graph = StateGraph(BicycleState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
