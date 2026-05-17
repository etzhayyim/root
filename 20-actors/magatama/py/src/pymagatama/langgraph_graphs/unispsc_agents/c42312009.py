from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class StaplerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_biocompatibility(state: StaplerState):
    errors = []
    if 'ISO-10993' not in state['spec_data'].get('certifications', []):
        errors.append('Missing ISO-10993 biocompatibility certification')
    return {'validation_errors': errors}

def check_sterilization(state: StaplerState):
    if not state['spec_data'].get('sterilization_method'):
        return {'validation_errors': state['validation_errors'] + ['Sterilization method missing']}
    return {}

builder = StateGraph(StaplerState)
builder.add_node('biocompatibility', validate_biocompatibility)
builder.add_node('sterilization', check_sterilization)
builder.add_edge('biocompatibility', 'sterilization')
builder.add_edge('sterilization', END)
builder.set_entry_point('biocompatibility')
graph = builder.compile()