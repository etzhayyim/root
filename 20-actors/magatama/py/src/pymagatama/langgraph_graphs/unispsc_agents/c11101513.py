from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_id: str
    purity: float
    safety_verified: bool
    compliance_tags: List[str]

def validate_purity(state: ChemicalState) -> ChemicalState:
    if state['purity'] < 0.99:
        raise ValueError('Purity below 99% standard')
    return state

def check_regulatory(state: ChemicalState) -> ChemicalState:
    state['safety_verified'] = True
    state['compliance_tags'] = ['REACH', 'GHS']
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('regulate', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulate')
graph.add_edge('regulate', END)
graph = graph.compile()
