from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class BioChemicalState(TypedDict):
    chemical_id: str
    purity_level: float
    safety_verified: bool
    compliance_tags: Annotated[Sequence[str], operator.add]

def validate_purity(state: BioChemicalState):
    is_pure = state['purity_level'] >= 99.9
    return {'safety_verified': is_pure}

def check_compliance(state: BioChemicalState):
    tags = ['dual-use-review'] if state['purity_level'] > 99.99 else ['standard']
    return {'compliance_tags': tags}

graph = StateGraph(BioChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()