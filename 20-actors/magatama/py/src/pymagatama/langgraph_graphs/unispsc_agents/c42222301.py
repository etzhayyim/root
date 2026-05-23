from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TransfusionKitState(TypedDict):
    kit_id: str
    compliance_docs: List[str]
    is_sterile: bool
    approved: bool

def validate_sterilization(state: TransfusionKitState) -> TransfusionKitState:
    state['is_sterile'] = True
    return state

def check_compliance(state: TransfusionKitState) -> TransfusionKitState:
    state['approved'] = all(d in state['compliance_docs'] for d in ['ISO_13485', 'CE_MARK'])
    return state

graph = StateGraph(TransfusionKitState)
graph.add_node('sterilization_check', validate_sterilization)
graph.add_node('compliance_review', check_compliance)
graph.set_entry_point('sterilization_check')
graph.add_edge('sterilization_check', 'compliance_review')
graph.add_edge('compliance_review', END)
graph = graph.compile()
