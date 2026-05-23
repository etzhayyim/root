from typing import TypedDict
from langgraph.graph import StateGraph, END

class OfficeFurnitureState(TypedDict):
    dimensions: dict
    material: str
    compliance_ok: bool

def validate_specs(state: OfficeFurnitureState) -> OfficeFurnitureState:
    # Logic to validate dimensions and materials against workstation standards
    state['compliance_ok'] = state['dimensions'].get('width', 0) <= 200
    return state

def check_stability(state: OfficeFurnitureState) -> str:
    return 'validate' if state['compliance_ok'] else END

graph = StateGraph(OfficeFurnitureState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
