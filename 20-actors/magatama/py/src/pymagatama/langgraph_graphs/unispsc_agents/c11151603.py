from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checked: bool
    safety_clearance: bool

def validate_composition(state: ChemicalState):
    # Simulate material composition and purity validation logic
    is_valid = state['purity_level'] >= 99.0
    return {'compliance_checked': is_valid}

def perform_safety_review(state: ChemicalState):
    # Simulate dangerous goods and dual-use regulation check
    return {'safety_clearance': True if state['compliance_checked'] else False}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_composition)
graph.add_node('safety', perform_safety_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)

compiled_graph = graph.compile()
