from typing import TypedDict
from langgraph.graph import StateGraph, END

class VetCardioState(TypedDict):
    product_id: str
    compliance_docs: list
    is_sterile: bool
    approved: bool

def validate_compliance(state: VetCardioState) -> VetCardioState:
    state['approved'] = all([len(state['compliance_docs']) > 0, state['is_sterile']])
    return state

def route_by_compliance(state: VetCardioState) -> str:
    return 'process' if state['approved'] else 'reject'

graph = StateGraph(VetCardioState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END, 'reject': END})
graph.compile()
