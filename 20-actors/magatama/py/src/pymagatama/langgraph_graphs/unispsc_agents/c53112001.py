from typing import TypedDict
from langgraph.graph import StateGraph, END
class ShoehornState(TypedDict):
    spec_data: dict
    is_approved: bool
def validate_specs(state: ShoehornState):
    state['is_approved'] = 'material_composition' in state['spec_data'] and 'length_mm' in state['spec_data']
    return state
graph = StateGraph(ShoehornState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()