from typing import TypedDict
from langgraph.graph import StateGraph, END

class ArtHorseState(TypedDict):
    spec_data: dict
    is_validated: bool

def validate_specs(state: ArtHorseState):
    required = ['material_type', 'weight_capacity_kg']
    validated = all(k in state['spec_data'] for k in required)
    return {'is_validated': validated}

graph = StateGraph(ArtHorseState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
