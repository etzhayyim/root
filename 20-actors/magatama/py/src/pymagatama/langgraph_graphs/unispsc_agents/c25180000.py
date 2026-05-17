from typing import TypedDict
from langgraph.graph import StateGraph, END

class VehicleState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_structural_spec(state: VehicleState):
    # Simulate CAD/Structural validation logic
    specs = state.get('spec_data', {})
    state['is_compliant'] = specs.get('load_capacity', 0) > 0
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(VehicleState)
graph.add_node('validate', validate_structural_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

compiled_graph = graph.compile()