from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas: str
    purity: float
    safety_check_passed: bool
    compliance_tags: List[str]

def validate_purity(state: ChemicalState) -> ChemicalState:
    if state['purity'] < 99.5:
        state['safety_check_passed'] = False
    else:
        state['safety_check_passed'] = True
    return state

def route_compliance(state: ChemicalState) -> str:
    return 'check_success' if state['safety_check_passed'] else 'check_failed'

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
