from typing import TypedDict
from langgraph.graph import StateGraph, END

class PoleState(TypedDict):
    specs: dict
    approved: bool

def validate_structural_specs(state: PoleState):
    required = ['wind_load', 'material_grade']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def check_corrosion_compliance(state: PoleState):
    state['approved'] = state['approved'] and state['specs'].get('coating') == 'galvanized'
    return state

graph = StateGraph(PoleState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('corrosion', check_corrosion_compliance)
graph.add_edge('validate', 'corrosion')
graph.add_edge('corrosion', END)
graph.set_entry_point('validate')
graph.compile()