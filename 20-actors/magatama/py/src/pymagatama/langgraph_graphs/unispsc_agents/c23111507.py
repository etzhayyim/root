from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RobotState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_payload(state: RobotState):
    if state['specs'].get('payload_capacity_kg', 0) <= 0:
        state['validation_errors'].append('Invalid payload capacity.')
    return 'check_safety'

def check_safety(state: RobotState):
    if 'safety_standard_compliance' not in state['specs']:
        state['validation_errors'].append('Missing safety certifications.')
    state['approved'] = len(state['validation_errors']) == 0
    return END

builder = StateGraph(RobotState)
builder.add_node('validate', validate_payload)
builder.add_node('safety', check_safety)
builder.set_entry_point('validate')
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
graph = builder.compile()
