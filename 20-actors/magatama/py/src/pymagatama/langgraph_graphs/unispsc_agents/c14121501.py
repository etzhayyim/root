from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    material_type: str
    shock_rating: float
    compliance_checked: bool
    approved: bool

def validate_cushioning(state: PackagingState):
    if state['shock_rating'] >= 0.8:
        return {'compliance_checked': True}
    return {'compliance_checked': False}

def approval_node(state: PackagingState):
    return {'approved': state['compliance_checked']}

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_cushioning)
graph.add_node('approve', approval_node)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
