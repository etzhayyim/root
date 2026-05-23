from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastingState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    is_approved: bool

def validate_dimension(state: CastingState):
    state['validation_results'].append('DIM_CHECK_PASSED')
    return 'validate_dimension'

def inspect_material_integrity(state: CastingState):
    state['validation_results'].append('MATERIAL_PASS')
    return 'inspect_material_integrity'

graph = StateGraph(CastingState)
graph.add_node('validate_dimension', validate_dimension)
graph.add_node('inspect_material_integrity', inspect_material_integrity)
graph.set_entry_point('validate_dimension')
graph.add_edge('validate_dimension', 'inspect_material_integrity')
graph.add_edge('inspect_material_integrity', END)
graph = graph.compile()
