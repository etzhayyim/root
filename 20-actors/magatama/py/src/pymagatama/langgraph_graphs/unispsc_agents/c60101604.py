from typing import TypedDict
from langgraph.graph import StateGraph, END

class CertificateState(TypedDict):
    material_spec: str
    quality_check: bool
    approved: bool

def validate_material(state: CertificateState):
    state['quality_check'] = state['material_spec'] in ['Leather', 'HeavyCardstock']
    return state

def approval_step(state: CertificateState):
    state['approved'] = state['quality_check']
    return state

graph = StateGraph(CertificateState)
graph.add_node('validate', validate_material)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()