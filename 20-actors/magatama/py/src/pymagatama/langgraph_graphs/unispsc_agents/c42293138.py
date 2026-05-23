from typing import TypedDict
from langgraph.graph import StateGraph, END

class UrologyState(TypedDict):
    part_id: str
    is_sterile: bool
    compliance_docs: list
    status: str

def validate_compliance(state: UrologyState):
    state['status'] = 'COMPLIANT' if state['is_sterile'] and len(state['compliance_docs']) > 0 else 'REJECTED'
    return state

def check_material(state: UrologyState):
    return {'status': 'VERIFIED_STEEL'}

graph = StateGraph(UrologyState)
graph.add_node('validate', validate_compliance)
graph.add_node('material', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'material')
graph.add_edge('material', END)
graph = graph.compile()
