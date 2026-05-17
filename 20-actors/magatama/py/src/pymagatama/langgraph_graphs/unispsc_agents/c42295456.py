from langgraph.graph import StateGraph, END
from typing import TypedDict

class SurgicalFeltState(TypedDict):
    material_type: str
    is_sterile: bool
    compliance_docs: list
    approval_status: bool

def validate_material(state: SurgicalFeltState):
    state['approval_status'] = state['is_sterile'] and 'ISO10993' in state['compliance_docs']
    return state

graph = StateGraph(SurgicalFeltState)
graph.add_node('verify', validate_material)
graph.set_entry_point('verify')
graph.add_edge('verify', END)
app = graph.compile()