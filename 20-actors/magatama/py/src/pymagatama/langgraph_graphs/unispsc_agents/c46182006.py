from langgraph.graph import StateGraph, END
from typing import TypedDict
class FilmProcurementState(TypedDict):
    material_type: str
    adhesion_level: float
    compliance_check: bool
    approved: bool
def validate_specs(state: FilmProcurementState):
    state['compliance_check'] = state['adhesion_level'] > 0 and len(state['material_type']) > 0
    return state
def finalize_order(state: FilmProcurementState):
    state['approved'] = state['compliance_check']
    return state
graph = StateGraph(FilmProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
