from typing import TypedDict
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    tool_type: str
    spec_check: bool
    is_compliant: bool

def validate_specs(state: PackagingState):
    state['spec_check'] = True if state['tool_type'] else False
    return state

def compliance_check(state: PackagingState):
    state['is_compliant'] = True
    return state

builder = StateGraph(PackagingState)
builder.add_node('validation', validate_specs)
builder.add_node('compliance', compliance_check)
builder.add_edge('validation', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validation')
graph = builder.compile()