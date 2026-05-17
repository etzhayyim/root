from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_id: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: BearingState) -> BearingState:
    specs = state.get('specs', {})
    # Simulated strict validation for high-precision components
    if 'load_capacity' in specs and specs['load_capacity'] > 0:
        state['validation_passed'] = True
        state['log'].append('Specs validated successfully')
    else:
        state['validation_passed'] = False
        state['log'].append('Validation failed: Missing or invalid load capacity')
    return state

def quality_control(state: BearingState) -> BearingState:
    if state['validation_passed']:
        state['log'].append('Quality check passed for high-precision bearing')
    return state

builder = StateGraph(BearingState)
builder.add_node('validate', validate_specs)
builder.add_node('qc', quality_control)
builder.add_edge('validate', 'qc')
builder.add_edge('qc', END)
builder.set_entry_point('validate')
graph = builder.compile()