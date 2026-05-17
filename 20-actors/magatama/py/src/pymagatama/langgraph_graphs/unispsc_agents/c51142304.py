from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: list[str]
    approved: bool

def validate_purity(state: ProcurementState):
    if state['purity'] >= 0.99:
        return {'approved': True}
    return {'approved': False}

def check_compliance(state: ProcurementState):
    return {'compliance_docs': ['GMP_CERT', 'MSDS']}

graph = StateGraph(ProcurementState)
graph.add_node('check_compliance', check_compliance)
graph.add_node('validate_purity', validate_purity)
graph.add_edge('check_compliance', 'validate_purity')
graph.add_edge('validate_purity', END)
graph.set_entry_point('check_compliance')