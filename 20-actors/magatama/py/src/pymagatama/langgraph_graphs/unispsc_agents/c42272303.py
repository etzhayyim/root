from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ResusDeviceState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    is_sterile: bool
    approved: bool

def validate_compliance(state: ResusDeviceState):
    if 'ISO_13485' in state['compliance_docs'] and state['is_sterile']:
        return {'approved': True}
    return {'approved': False}

def route_verification(state: ResusDeviceState):
    return 'validate' if state['approved'] is None else END

graph = StateGraph(ResusDeviceState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()