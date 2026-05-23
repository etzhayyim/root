from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class WoodenPaletteState(TypedDict):
    material_compliance: bool
    is_fumigated: bool
    load_limit_kg: float
    inspection_passed: bool

def validate_phytosanitary(state: WoodenPaletteState) -> WoodenPaletteState:
    state['is_fumigated'] = True
    return state

def check_structural_integrity(state: WoodenPaletteState) -> WoodenPaletteState:
    state['inspection_passed'] = state['load_limit_kg'] > 0
    return state

graph = StateGraph(WoodenPaletteState)
graph.add_node('phyto_check', validate_phytosanitary)
graph.add_node('structural_check', check_structural_integrity)
graph.add_edge('phyto_check', 'structural_check')
graph.add_edge('structural_check', END)
graph.set_entry_point('phyto_check')
graph = graph.compile()
