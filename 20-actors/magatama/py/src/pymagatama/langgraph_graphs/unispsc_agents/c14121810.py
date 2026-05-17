from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    dimensions: dict
    material_spec: str
    validation_passed: bool
    log: List[str]

def validate_dimensions(state: PackagingState):
    # Simulate CAD validation logic
    is_valid = state['dimensions'].get('l', 0) > 0 and state['dimensions'].get('w', 0) > 0
    return {'validation_passed': is_valid, 'log': ['Dimension check completed']}

def process_material(state: PackagingState):
    # Simulate material structural verification
    return {'log': state['log'] + ['Material structural verification passed']}

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_dimensions)
graph.add_node('material', process_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'material')
graph.add_edge('material', END)

graph = graph.compile()