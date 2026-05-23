from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ChemicalState(TypedDict):
    material_id: str
    purity_level: float
    safety_checks: List[str]
    is_cleared: bool

def validate_purity(state: ChemicalState):
    cleared = state['purity_level'] >= 0.99
    return {'is_cleared': cleared, 'safety_checks': state['safety_checks'] + ['purity_validated']}

def perform_safety_scan(state: ChemicalState):
    return {'safety_checks': state['safety_checks'] + ['safety_scan_complete']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', perform_safety_scan)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
