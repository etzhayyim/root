from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_name: str
    purity_level: float
    has_sds: bool
    is_approved: bool

def validate_purity(state: ChemicalState):
    state['is_approved'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: ChemicalState):
    state['is_approved'] = state['is_approved'] and state['has_sds']
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()