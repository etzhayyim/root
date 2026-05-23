from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalDeviceState(TypedDict):
    device_type: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: DentalDeviceState):
    required = ['ISO_13485', 'CE_Mark']
    approved = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': approved}

def route_by_type(state: DentalDeviceState):
    return 'process_device'

graph_builder = StateGraph(DentalDeviceState)
graph_builder.add_node('validate', validate_compliance)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()
