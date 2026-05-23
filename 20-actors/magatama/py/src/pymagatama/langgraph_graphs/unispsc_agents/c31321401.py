from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AluminumAssemblyState(TypedDict):
    part_specs: dict
    validation_results: List[str]
    approved: bool

def validate_material(state: AluminumAssemblyState):
    # Simulate material compliance check
    is_valid = 'alloy_grade' in state['part_specs']
    return {'validation_results': ['Material check passed' if is_valid else 'Material check failed']}

def validate_welding(state: AluminumAssemblyState):
    # Simulate weld inspection process
    return {'validation_results': state['validation_results'] + ['Weld verification successful']}

graph = StateGraph(AluminumAssemblyState)
graph.add_node('material_check', validate_material)
graph.add_node('weld_check', validate_welding)
graph.add_edge('material_check', 'weld_check')
graph.add_edge('weld_check', END)
graph.set_entry_point('material_check')
graph = graph.compile()
