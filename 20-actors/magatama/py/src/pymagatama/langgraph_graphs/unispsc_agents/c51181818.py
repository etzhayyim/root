from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity: float
    compliance_docs: List[str]
    validated: bool

def validate_purity(state: ProcurementState) -> dict:
    is_valid = state['purity'] >= 99.0
    return {'validated': is_valid}

def check_compliance(state: ProcurementState) -> dict:
    has_coa = 'COA' in state['compliance_docs']
    return {'validated': state['validated'] and has_coa}

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
