from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specifications: dict
    validation_passed: bool
    compliance_tags: List[str]

def validate_alloy(state: CastingState):
    alloy = state['specifications'].get('alloy_type')
    return {'validation_passed': alloy in ['C83600', 'C90300']}

def check_compliance(state: CastingState):
    tags = ['dual-use-export-control'] if state['validation_passed'] else []
    return {'compliance_tags': tags}

builder = StateGraph(CastingState)
builder.add_node('validate', validate_alloy)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()