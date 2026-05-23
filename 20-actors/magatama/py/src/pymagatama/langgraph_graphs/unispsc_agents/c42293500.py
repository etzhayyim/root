from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_id: str
    compliance_docs: list
    is_sterile: bool
    is_approved: bool

def validate_compliance(state: SurgicalDeviceState):
    state['is_approved'] = len(state['compliance_docs']) > 0 and state['is_sterile']
    return state

workflow = StateGraph(SurgicalDeviceState)
workflow.add_node('compliance_validation', validate_compliance)
workflow.set_entry_point('compliance_validation')
workflow.add_edge('compliance_validation', END)
graph = workflow.compile()
