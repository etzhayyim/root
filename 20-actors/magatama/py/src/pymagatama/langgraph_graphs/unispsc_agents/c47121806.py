from typing import TypedDict
from langgraph.graph import StateGraph, END

class MopOrderState(TypedDict):
    material: str
    compatibility_check: bool
    approved: bool

def validate_materials(state: MopOrderState):
    allowed = ['plastic', 'stainless_steel']
    return {'compatibility_check': state['material'] in allowed}

def approval_step(state: MopOrderState):
    return {'approved': state['compatibility_check']}

graph = StateGraph(MopOrderState)
graph.add_node('validate', validate_materials)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()