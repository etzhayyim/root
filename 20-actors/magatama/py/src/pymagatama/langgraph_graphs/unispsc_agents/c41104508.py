from typing import TypedDict
from langgraph.graph import StateGraph, END

class InductionDryerState(TypedDict):
    temp_req: float
    safety_check_passed: bool
    validation_log: list

def validate_specs(state: InductionDryerState):
    passed = state['temp_req'] > 0
    return {'safety_check_passed': passed, 'validation_log': ['Specs validated']}

def conduct_risk_assessment(state: InductionDryerState):
    return {'validation_log': state['validation_log'] + ['Risk assessment complete']}

builder = StateGraph(InductionDryerState)
builder.add_node('specs', validate_specs)
builder.add_node('risk', conduct_risk_assessment)
builder.add_edge('specs', 'risk')
builder.add_edge('risk', END)
builder.set_entry_point('specs')
graph = builder.compile()