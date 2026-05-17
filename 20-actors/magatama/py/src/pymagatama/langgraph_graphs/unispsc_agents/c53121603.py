from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BackpackState(TypedDict):
    material: str
    volume_liters: int
    is_waterproof: bool
    validation_errors: List[str]

def validate_materials(state: BackpackState) -> BackpackState:
    if state.get('material', '') not in ['Nylon', 'Polyester', 'Canvas']:
        state['validation_errors'].append('Unsupported material type detected.')
    return state

def check_capacity(state: BackpackState) -> BackpackState:
    if state.get('volume_liters', 0) < 5:
        state['validation_errors'].append('Capacity too low for standard backpack.')
    return state

graph = StateGraph(BackpackState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_capacity', check_capacity)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_capacity')
graph.add_edge('check_capacity', END)
compile_graph = graph.compile()