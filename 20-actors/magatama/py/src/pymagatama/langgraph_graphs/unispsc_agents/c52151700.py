from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material: str
    compliance_docs: bool
    is_approved: bool

def validate_material(state: ProcurementState):
    state['is_approved'] = state['material'] in ['18/8', '18/10', 'Ceramic']
    return state

def check_certification(state: ProcurementState):
    if state['is_approved'] and state['compliance_docs']:
        return 'complete'
    return 'incomplete'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()