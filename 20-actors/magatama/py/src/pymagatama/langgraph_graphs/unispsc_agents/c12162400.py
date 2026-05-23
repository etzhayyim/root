from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    material_id: str
    quality_checks: List[str]
    is_compliant: bool

def validate_composition(state: AdhesiveState) -> AdhesiveState:
    # Logic to verify chemical composition against safety specs
    state['quality_checks'].append('COMPOSITION_VERIFIED')
    state['is_compliant'] = True
    return state

def check_shelf_life(state: AdhesiveState) -> AdhesiveState:
    # Logic to check shelf life requirements
    state['quality_checks'].append('SHELF_LIFE_VALIDATED')
    return state

graph = StateGraph(AdhesiveState)
graph.add_node('validate_comp', validate_composition)
graph.add_node('check_shelf', check_shelf_life)
graph.set_entry_point('validate_comp')
graph.add_edge('validate_comp', 'check_shelf')
graph.add_edge('check_shelf', END)
graph = graph.compile()
