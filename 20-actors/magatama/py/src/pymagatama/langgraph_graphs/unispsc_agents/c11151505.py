from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    safety_verified: bool
    compliant: bool

def validate_purity(state: ChemicalState):
    return {'safety_verified': state['purity'] >= 99.9}

def check_compliance(state: ChemicalState):
    return {'compliant': state['safety_verified']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
