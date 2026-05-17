from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class ForgingState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_tags: List[str]
def validate_material(state: ForgingState) -> ForgingState:
    material = state['specs'].get('material_grade')
    state['validation_passed'] = material is not None
    return state
def check_dimensions(state: ForgingState) -> ForgingState:
    if state['validation_passed']:
        state['validation_passed'] = 'dimensional_tolerances' in state['specs']
    return state
graph = StateGraph(ForgingState)
graph.add_node('validate', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
graph.set_entry_point('validate')
graph = graph.compile()