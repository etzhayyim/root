from langgraph.graph import StateGraph
from typing import TypedDict, List

class PipeCleanerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_materials(state: PipeCleanerState) -> PipeCleanerState:
    materials = state['spec_data'].get('materials', [])
    if not all(m in ['cotton', 'synthetic_fiber'] for m in materials):
        state['validation_errors'].append('Invalid material type detected.')
    return state

def check_dimensions(state: PipeCleanerState) -> PipeCleanerState:
    if state['spec_data'].get('diameter_mm', 0) > 5:
        state['validation_errors'].append('Diameter exceeds standard pipe gauge.')
    return state

def finalize_check(state: PipeCleanerState) -> PipeCleanerState:
    state['is_approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(PipeCleanerState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.add_node('finalize', finalize_check)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', 'finalize')
graph.add_edge('finalize', None)

compiled_graph = graph.compile()