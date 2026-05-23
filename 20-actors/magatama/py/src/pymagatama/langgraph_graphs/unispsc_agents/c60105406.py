from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    content_type: str
    compliance_verified: bool
    final_approval: bool

def validate_material(state: ProcurementState):
    # Business logic for home buying guide compliance check
    state['compliance_verified'] = True
    return 'approved'

def finalize_document(state: ProcurementState):
    state['final_approval'] = True
    return 'done'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_document)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
