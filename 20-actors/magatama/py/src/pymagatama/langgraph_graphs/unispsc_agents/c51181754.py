from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ChemicalState(TypedDict):
    purity: float
    compliance_docs: List[str]
    status: str

def validate_purity(state: ChemicalState):
    is_pure = state['purity'] >= 99.0
    return {'status': 'PASSED' if is_pure else 'FAILED'}

workflow = StateGraph(ChemicalState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()