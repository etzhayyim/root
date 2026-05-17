from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    sensor_id: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: SensorState) -> SensorState:
    state['validation_passed'] = all(k in state['specs'] for k in ['ip_rating', 'response_time_ms'])
    state['log'].append('Specs validation completed')
    return state

def check_compliance(state: SensorState) -> SensorState:
    if state['validation_passed']:
        state['log'].append('Compliance check passed for industrial sensor')
    return state

builder = StateGraph(SensorState)
builder.add_node('validate', validate_specs)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()