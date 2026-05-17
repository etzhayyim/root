from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_requirements: dict
    validation_passed: bool

def validate_uniform_specs(state: ProcurementState):
    # Business logic for nursing uniform compliance
    required_keys = ['antimicrobial_certification', 'fabric_composition']
    passed = all(k in state['spec_requirements'] for k in required_keys)
    return {'validation_passed': passed}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_uniform_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()