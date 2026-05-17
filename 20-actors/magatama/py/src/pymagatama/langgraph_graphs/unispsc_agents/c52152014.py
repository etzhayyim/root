from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_safety_test: bool
    thermal_rating_confirmed: bool
    is_approved: bool

def validate_specs(state: ProcurementState):
    state['is_approved'] = state.get('material_safety_test') and state.get('thermal_rating_confirmed')
    return 'end'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compiled_graph = graph.compile()