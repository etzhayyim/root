from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToxicologyWorkflowState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_log: list

def validate_specs(state: ToxicologyWorkflowState):
    required = ['calibration_certificate', 'detection_limit']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_status': valid}

def alert_compliance(state: ToxicologyWorkflowState):
    if not state.get('validation_status'):
        print('Alert: Missing documentation for regulated medical device')
    return state

builder = StateGraph(ToxicologyWorkflowState)
builder.add_node('validate', validate_specs)
builder.add_node('alert', alert_compliance)
builder.add_edge('validate', 'alert')
builder.add_edge('alert', END)
builder.set_entry_point('validate')
graph = builder.compile()
