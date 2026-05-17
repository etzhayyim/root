from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity_level: float
    qc_passed: bool
    specs_verified: bool

def validate_purity(state: ChemicalProcurementState):
    state['qc_passed'] = state['purity_level'] >= 99.9
    return state

def verify_specs(state: ChemicalProcurementState):
    state['specs_verified'] = True
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_specs', verify_specs)
graph.add_edge('validate_purity', 'verify_specs')
graph.add_edge('verify_specs', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()