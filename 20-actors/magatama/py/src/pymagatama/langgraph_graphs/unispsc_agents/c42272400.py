from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThoracentesisState(TypedDict):
    product_id: str
    is_sterile: bool
    compliant: bool
    approval_status: str

def check_compliance(state: ThoracentesisState):
    state['compliant'] = state['is_sterile'] and True
    return {'approval_status': 'APPROVED' if state['compliant'] else 'REJECTED'}

graph = StateGraph(ThoracentesisState)
graph.add_node('validate_compliance', check_compliance)
graph.set_entry_point('validate_compliance')
graph.add_edge('validate_compliance', END)
graph = graph.compile()