from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasAnalyzerState(TypedDict):
    spec_data: dict
    validation_errors: list[str]
    is_compliant: bool

def validate_absorbent_compatibility(state: GasAnalyzerState):
    errors = []
    reagent = state['spec_data'].get('absorbent_reagent')
    if not reagent:
        errors.append('Missing required absorbent reagent specification')
    return {'validation_errors': errors}

def check_compliance(state: GasAnalyzerState):
    is_valid = len(state['validation_errors']) == 0
    return {'is_compliant': is_valid}

builder = StateGraph(GasAnalyzerState)
builder.add_node('validate', validate_absorbent_compatibility)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()