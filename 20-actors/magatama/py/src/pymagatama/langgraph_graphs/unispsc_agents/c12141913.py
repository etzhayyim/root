from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity: float
    status: str
    log: List[str]

def validate_purity(state: ChemicalState) -> ChemicalState:
    if state['purity'] >= 99.9:
        state['status'] = 'Purity Verified'
    else:
        state['status'] = 'Rejected: Insufficient Purity'
    return state

def check_compliance(state: ChemicalState) -> ChemicalState:
    state['log'].append('Compliance checked for dual-use control')
    return state

workflow = StateGraph(ChemicalState)
workflow.add_node('validate', validate_purity)
workflow.add_node('compliance', check_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()
