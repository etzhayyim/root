from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalProcessingState(TypedDict):
    commodity_code: str
    purity_level: float
    stability_check: bool
    safety_clearance: bool

def validate_purity(state: ChemicalProcessingState):
    # Simulate CAD/Spec validation for chemical intermediate
    is_pure = state['purity_level'] >= 0.99
    return {'purity_level': state['purity_level'], 'stability_check': is_pure}

def perform_safety_scan(state: ChemicalProcessingState):
    # Compliance check for dual-use/regulated goods
    return {'safety_clearance': True}

graph = StateGraph(ChemicalProcessingState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('safety_scan', perform_safety_scan)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'safety_scan')
graph.add_edge('safety_scan', END)

compile = graph.compile()