from typing import TypedDict
from langgraph.graph import StateGraph, END
class SurgicalKitState(TypedDict):
    kit_id: str
    compliance_docs: list
    is_sterile: bool
    approved: bool
def validate_compliance(state: SurgicalKitState):
    state['approved'] = all(['ISO_13485' in doc for doc in state['compliance_docs']])
    return state
def update_status(state: SurgicalKitState):
    state['is_sterile'] = True
    return state
graph = StateGraph(SurgicalKitState)
graph.add_node('validate', validate_compliance)
graph.add_node('mark_sterile', update_status)
graph.add_edge('validate', 'mark_sterile')
graph.add_edge('mark_sterile', END)
graph.set_entry_point('validate')
graph = graph.compile()
