from typing import TypedDict
from langgraph.graph import StateGraph, END

class RiddleState(TypedDict):
    mesh_size: float
    material: str
    is_compliant: bool

def validate_specs(state: RiddleState) -> RiddleState:
    state['is_compliant'] = state['mesh_size'] > 0 and state['material'] in ['stainless_steel', 'galvanized_steel']
    return state

def determine_next_step(state: RiddleState) -> str:
    return 'process' if state['is_compliant'] else END

graph = StateGraph(RiddleState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', determine_next_step)
graph.add_edge('process', END)
graph = graph.compile()