from typing import TypedDict
from langgraph.graph import StateGraph, END

class NonivamideState(TypedDict):
    purity: float
    compliance_docs: list
    status: str

def validate_compliance(state: NonivamideState):
    if state['purity'] >= 99.0 and 'MSDS' in state['compliance_docs']:
        return {'status': 'approved'}
    return {'status': 'rejected'}

builder = StateGraph(NonivamideState)
builder.add_node('compliance', validate_compliance)
builder.set_entry_point('compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
