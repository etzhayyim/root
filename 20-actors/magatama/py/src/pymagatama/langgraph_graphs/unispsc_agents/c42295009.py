from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_type: str
    compliance_docs: List[str]
    validation_status: bool

def validate_specs(state: SurgicalDeviceState):
    required = ['ISO_13485', 'Biocompatibility_Cert', 'Sterilization_Report']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'validation_status': all_present}

def route_verification(state: SurgicalDeviceState):
    return 'valid' if state['validation_status'] else 'reject'

graph = StateGraph(SurgicalDeviceState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate') # Note: Placeholder for actual entry logic
graph.compile()
