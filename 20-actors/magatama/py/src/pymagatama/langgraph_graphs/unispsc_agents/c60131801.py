from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class State(TypedDict):
    scarf_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_materials(state: State) -> State:
    material = state.get('scarf_specs', {}).get('material', '')
    if not material:
        state['validation_errors'].append('Material missing')
    return state

def check_dimensions(state: State) -> State:
    if state.get('scarf_specs', {}).get('size_cm', 0) < 50:
        state['validation_errors'].append('Size too small for performance')
    return state

graph = StateGraph(State)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()
