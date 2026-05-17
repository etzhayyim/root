from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SharpenerState(TypedDict):
    instrument_type: str
    grit_level: int
    compliance_docs: List[str]
    is_approved: bool

def validate_grit(state: SharpenerState) -> SharpenerState:
    # Logic to ensure grit matches surgical needs
    state['is_approved'] = state['grit_level'] > 1000
    return state

def verify_docs(state: SharpenerState) -> SharpenerState:
    state['is_approved'] = state['is_approved'] and len(state['compliance_docs']) > 0
    return state

graph = StateGraph(SharpenerState)
graph.add_node('validate', validate_grit)
graph.add_node('verify', verify_docs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'verify')
graph.add_edge('verify', END)
graph = graph.compile()