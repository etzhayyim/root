from typing import TypedDict
from langgraph.graph import StateGraph, END
class ContainerState(TypedDict):
    compliance_checked: bool
    hazard_rating: str
    approval_status: str
def check_hazard_compliance(state: ContainerState):
    state['compliance_checked'] = state['hazard_rating'] == 'certified'
    return state
def update_approval(state: ContainerState):
    state['approval_status'] = 'APPROVED' if state['compliance_checked'] else 'REJECTED'
    return state
graph = StateGraph(ContainerState)
graph.add_node('verify', check_hazard_compliance)
graph.add_node('approve', update_approval)
graph.set_entry_point('verify')
graph.add_edge('verify', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
