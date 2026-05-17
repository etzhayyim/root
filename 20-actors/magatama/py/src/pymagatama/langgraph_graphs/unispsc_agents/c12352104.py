from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    batch_id: str
    purity: float
    safety_check_passed: bool
    log: Annotated[list[str], operator.add]

def validate_purity(state: ChemicalState) -> ChemicalState:
    passed = state['purity'] >= 99.9
    return {'safety_check_passed': passed, 'log': [f'Purity validation: {passed}']}

def check_compliance(state: ChemicalState) -> ChemicalState:
    return {'log': ['Compliance check: Verified MSDA/Hazmat protocols.']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()