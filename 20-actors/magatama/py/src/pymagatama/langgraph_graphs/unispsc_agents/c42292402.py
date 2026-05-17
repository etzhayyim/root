from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalProcurementState(TypedDict):
    device_id: str
    compliance_passed: bool
    sterility_verified: bool

def validate_certification(state: SurgicalProcurementState):
    # Simulate ISO 13485 validation
    state['compliance_passed'] = True
    return 'check_sterility'

def check_sterility(state: SurgicalProcurementState):
    # Simulate sterility documentation audit
    state['sterility_verified'] = True
    return 'end'

graph = StateGraph(SurgicalProcurementState)
graph.add_node('validate_certification', validate_certification)
graph.add_node('check_sterility', check_sterility)
graph.set_entry_point('validate_certification')
graph.add_edge('validate_certification', 'check_sterility')
graph.add_edge('check_sterility', END)

compiled_graph = graph.compile()