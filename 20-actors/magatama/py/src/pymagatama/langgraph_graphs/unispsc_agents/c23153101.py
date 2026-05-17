from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class RobotAttachmentState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_payload_specs(state: RobotAttachmentState):
    spec = state['spec_data']
    payload = spec.get('payload_capacity_kg', 0)
    valid = 0 < payload < 500
    return {'validation_results': [f'Payload {payload}kg valid: {valid}'], 'is_approved': valid}

def check_compliance(state: RobotAttachmentState):
    spec = state['spec_data']
    compliant = 'ISO' in spec.get('safety_standard_compliance', '')
    return {'validation_results': state['validation_results'] + [f'ISO compliant: {compliant}'], 'is_approved': state['is_approved'] and compliant}

graph = StateGraph(RobotAttachmentState)
graph.add_node('validate_payload', validate_payload_specs)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_payload')
graph.add_edge('validate_payload', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()