from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity_percentage: float
    safety_verified: bool
    compliance_docs: list[str]

def validate_purity(state: ChemicalState):
    is_pure = state['purity_percentage'] >= 99.9
    return {'safety_verified': is_pure}

def check_compliance(state: ChemicalState):
    is_compliant = len(state['compliance_docs']) >= 3
    return {'safety_verified': state['safety_verified'] and is_compliant}

graph = StateGraph(ChemicalState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_purity')
compiled_graph = graph.compile()