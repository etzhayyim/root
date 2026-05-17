from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    hazard_level: int
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: ChemicalState) -> ChemicalState:
    state['approved'] = state['purity'] >= 99.9
    return state

def check_hazard_compliance(state: ChemicalState) -> ChemicalState:
    if state['hazard_level'] > 5 and not state['compliance_docs']:
        state['approved'] = False
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_hazard_compliance', check_hazard_compliance)
graph.add_edge('validate_purity', 'check_hazard_compliance')
graph.add_edge('check_hazard_compliance', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()