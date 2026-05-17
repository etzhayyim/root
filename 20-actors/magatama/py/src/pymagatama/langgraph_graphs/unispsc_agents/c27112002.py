from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpadeState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_durability(state: SpadeState):
    blade = state['spec_data'].get('blade_material_grade', '')
    return {'is_compliant': blade in ['Carbon Steel', 'Stainless Steel']}

def decision_node(state: SpadeState):
    return 'valid' if state['is_compliant'] else END

graph = StateGraph(SpadeState)
graph.add_node('validate', validate_durability)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()