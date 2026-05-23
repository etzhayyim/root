from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity: float
    origin: str
    safety_check_passed: bool
    export_license_required: bool

def validate_composition(state: MineralState) -> MineralState:
    # Logic to validate chemical composition against industrial standards
    state['safety_check_passed'] = state['purity'] >= 95.0
    return state

def check_export_controls(state: MineralState) -> MineralState:
    # Logic to determine if material is subject to dual-use controls
    state['export_license_required'] = state['origin'] in ['restricted_zone_a', 'restricted_zone_b']
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_composition)
graph.add_node('export_check', check_export_controls)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
