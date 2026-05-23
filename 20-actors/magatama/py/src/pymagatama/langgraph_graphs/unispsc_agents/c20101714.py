from typing import TypedDict, Annotated; from langgraph.graph import StateGraph, END; import operator

class RobotState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_payload(state: RobotState):
    payload = state['spec_data'].get('payload_capacity_kg', 0)
    valid = 0 < payload < 50
    return {'validation_results': ['Payload within safe range' if valid else 'Payload limit exceeded']}

def check_compliance(state: RobotState):
    compliance = state['spec_data'].get('iso_certification_compliance', False)
    return {'is_approved': compliance}

workflow = StateGraph(RobotState)
workflow.add_node('validate', validate_payload)
workflow.add_node('compliance', check_compliance)
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
