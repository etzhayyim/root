from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AppState(TypedDict):
    product_id: str
    is_sterile: bool
    compliance_docs: List[str]
    status: str

def validate_sterility(state: AppState) -> AppState:
    state['status'] = 'VALIDATED' if state['is_sterile'] else 'REJECTED'
    return state

def check_compliance(state: AppState) -> AppState:
    if len(state['compliance_docs']) >= 2:
        state['status'] = 'APPROVED'
    else:
        state['status'] = 'PENDING_DOCS'
    return state

graph = StateGraph(AppState)
graph.add_node('validate', validate_sterility)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()