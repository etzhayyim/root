from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ComputerSpecState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_hardware(state: ComputerSpecState):
    errors = []
    if state['specs'].get('RAM_capacity_GB', 0) < 8:
        errors.append('Insufficient RAM for modern business standards.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def security_check(state: ComputerSpecState):
    if not state.get('specs', {}).get('Security_chip_TPM_version'):
        state['validation_errors'].append('Missing mandatory TPM module.')
    return state

builder = StateGraph(ComputerSpecState)
builder.add_node('validate', validate_hardware)
builder.add_node('security', security_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'security')
builder.add_edge('security', END)
graph = builder.compile()