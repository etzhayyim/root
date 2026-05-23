from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PartitionState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: PartitionState):
    dims = state['spec_data'].get('dimensions', {})
    if dims.get('length', 0) <= 0 or dims.get('width', 0) <= 0:
        state['validation_errors'].append('Invalid dimensions provided')
    return state

def check_material_compliance(state: PartitionState):
    if state['spec_data'].get('material') not in ['Steel', 'Polypropylene', 'Acrylic']:
        state['validation_errors'].append('Unsupported material')
    return state

graph = StateGraph(PartitionState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_material_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
