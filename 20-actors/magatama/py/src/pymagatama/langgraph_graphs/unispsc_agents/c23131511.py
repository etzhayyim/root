from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    specifications: dict
    compliance_check: bool
    validation_log: List[str]

def validate_payload(state: RobotProcurementState):
    payload = state['specifications'].get('payload', 0)
    valid = payload > 0
    return {'compliance_check': valid, 'validation_log': [f'Payload validated: {payload}kg']}

def check_compliance(state: RobotProcurementState):
    iso_req = state['specifications'].get('iso_standard', False)
    return {'compliance_check': iso_req}

graph = StateGraph(RobotProcurementState)
graph.add_node('payload_check', validate_payload)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('payload_check')
graph.add_edge('payload_check', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()