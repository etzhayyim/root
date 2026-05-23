from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ChemicalState(TypedDict):
    material_name: str
    purity_level: float
    compliance_checked: bool
    safety_clearance: bool

def validate_purity(state: ChemicalState):
    state['compliance_checked'] = state['purity_level'] >= 99.0
    return state

def verify_safety(state: ChemicalState):
    state['safety_clearance'] = True
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_safety', verify_safety)
graph.add_edge('validate_purity', 'verify_safety')
graph.add_edge('verify_safety', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()
