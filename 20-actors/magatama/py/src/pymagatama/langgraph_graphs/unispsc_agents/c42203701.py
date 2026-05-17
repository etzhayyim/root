from typing import TypedDict
from langgraph.graph import StateGraph, END

class WorkflowState(TypedDict):
    device_id: str
    compliance_checked: bool
    image_data_verified: bool

def check_compliance(state: WorkflowState):
    state['compliance_checked'] = True
    return 'compliance_verified'

def verify_imaging_parameters(state: WorkflowState):
    state['image_data_verified'] = True
    return 'data_verified'

graph = StateGraph(WorkflowState)
graph.add_node('compliance', check_compliance)
graph.add_node('imaging', verify_imaging_parameters)
graph.add_edge('compliance', 'imaging')
graph.add_edge('imaging', END)
graph.set_entry_point('compliance')
graph = graph.compile()