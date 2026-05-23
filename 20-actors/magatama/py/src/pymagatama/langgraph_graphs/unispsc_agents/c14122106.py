from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    material_type: str
    thickness: float
    width: float
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: PackagingState) -> PackagingState:
    if not state['material_type'] in ['PE', 'PP', 'PVC']:
        state['validation_errors'].append('Unsupported material type')
    return state

def check_dimensions(state: PackagingState) -> PackagingState:
    if state['thickness'] < 10.0:
        state['validation_errors'].append('Thickness below industrial standard')
    state['is_approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_material)
graph.add_node('check_dims', check_dimensions)
graph.add_edge('validate', 'check_dims')
graph.add_edge('check_dims', END)
graph.set_entry_point('validate')
graph = graph.compile()
