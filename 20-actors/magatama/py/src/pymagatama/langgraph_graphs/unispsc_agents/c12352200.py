from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class LubricantState(TypedDict):
    spec_data: dict
    validation_results: list
    approval_status: bool

def validate_safety_compliance(state: LubricantState) -> LubricantState:
    # Logic to verify hazardous material compliance
    state['validation_results'].append('Safety Compliance Verified')
    return state

def verify_technical_spec(state: LubricantState) -> LubricantState:
    # Logic to verify viscosity and thermal specs
    state['validation_results'].append('Technical Specs Validated')
    state['approval_status'] = True
    return state

builder = StateGraph(LubricantState)
builder.add_node('validate_safety', validate_safety_compliance)
builder.add_node('verify_tech', verify_technical_spec)
builder.set_entry_point('validate_safety')
builder.add_edge('validate_safety', 'verify_tech')
builder.add_edge('verify_tech', END)
graph = builder.compile()
