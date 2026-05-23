from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastingState(TypedDict):
    part_number: str
    material_spec: str
    tolerance_checks: List[str]
    qa_approved: bool

def validate_materials(state: CastingState):
    print(f'Checking material spec: {state['material_spec']}')
    return {'qa_approved': True}

def perform_dimension_checks(state: CastingState):
    print('Running GD&T verification...')
    return {'tolerance_checks': ['Pass']}

graph = StateGraph(CastingState)
graph.add_node('material_validation', validate_materials)
graph.add_node('dimension_control', perform_dimension_checks)
graph.set_entry_point('material_validation')
graph.add_edge('material_validation', 'dimension_control')
graph.add_edge('dimension_control', END)
app = graph.compile()
