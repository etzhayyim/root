from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScopeState(TypedDict):
    device_type: str
    compliance_docs: list
    is_approved: bool

def validate_compliance(state: ScopeState):
    state['is_approved'] = all(['ISO_13485' in doc for doc in state['compliance_docs']])
    return state

def check_device_type(state: ScopeState):
    return 'ophthalmology' if 'ophthalmoscope' in state['device_type'] else 'otolaryngology'

graph = StateGraph(ScopeState)
graph.add_node('validate', validate_compliance)
graph.add_node('classify', check_device_type)
graph.set_entry_point('validate')
graph.add_edge('validate', 'classify')
graph.add_edge('classify', END)
graph = graph.compile()