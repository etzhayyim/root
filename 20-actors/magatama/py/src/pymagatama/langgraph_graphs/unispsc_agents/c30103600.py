from typing import TypedDict
from langgraph.graph import StateGraph, END

class StructuralState(TypedDict):
    spec_sheet: dict
    approved: bool

def validate_materials(state: StructuralState):
    grade = state['spec_sheet'].get('grade')
    state['approved'] = grade in ['SS400', 'SN490']
    return state

def approval_step(state: StructuralState):
    return {'approved': state['approved']}

graph = StateGraph(StructuralState)
graph.add_node('validate', validate_materials)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()