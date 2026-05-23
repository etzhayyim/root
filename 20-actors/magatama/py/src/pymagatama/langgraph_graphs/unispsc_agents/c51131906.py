from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PentastarchState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: List[str]
    validation_status: bool

def validate_purity(state: PentastarchState):
    state['validation_status'] = state['purity_level'] >= 99.5
    return state

def check_compliance(state: PentastarchState):
    return {'validation_status': state['validation_status'] and len(state['compliance_docs']) > 0}

workflow = StateGraph(PentastarchState)
workflow.add_node('validate_purity', validate_purity)
workflow.add_node('check_compliance', check_compliance)
workflow.add_edge('validate_purity', 'check_compliance')
workflow.add_edge('check_compliance', END)
workflow.set_entry_point('validate_purity')
graph = workflow.compile()
