from typing import TypedDict
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    dimensions: dict
    material_spec: str
    validation_passed: bool

def validate_dimensions(state: PackagingState):
    # Simulate CAD/Dimension validation logic
    state['validation_passed'] = all(v > 0 for v in state['dimensions'].values())
    return state

def check_material_compliance(state: PackagingState):
    # Simulate material compliance check
    if state['material_spec'] == 'Recyclable':
        print('Compliance check passed')
    return state

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_material_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
