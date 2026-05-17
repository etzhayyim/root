from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrassComponentState(TypedDict):
    part_id: str
    specs: dict
    validation_results: List[str]
    approved: bool

def validate_material(state: BrassComponentState):
    grade = state['specs'].get('MaterialGrade')
    is_valid = grade == 'C26000'
    return {'validation_results': [f'Material check: {is_valid}']}

def validate_dimensions(state: BrassComponentState):
    tol = state['specs'].get('Tolerance', 0.05)
    is_pass = tol <= 0.05
    return {'validation_results': state['validation_results'] + [f'Tolerance check: {is_pass}']}

graph = StateGraph(BrassComponentState)
graph.add_node('material_check', validate_material)
graph.add_node('dimension_check', validate_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', END)
app = graph.compile()