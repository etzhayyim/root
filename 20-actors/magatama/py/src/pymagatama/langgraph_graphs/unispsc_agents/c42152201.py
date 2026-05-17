from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalFoilState(TypedDict):
    foil_thickness: float
    purity_level: float
    certification_valid: bool
    approved: bool

def validate_specs(state: DentalFoilState):
    state['approved'] = state['foil_thickness'] < 0.05 and state['purity_level'] > 0.99 and state['certification_valid']
    return state

graph = StateGraph(DentalFoilState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()