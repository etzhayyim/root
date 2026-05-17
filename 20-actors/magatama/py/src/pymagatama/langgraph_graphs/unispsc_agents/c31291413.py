from typing import TypedDict
from langgraph.graph import StateGraph, END
class ExtrusionState(TypedDict):
    material_spec: str
    tolerance_check: bool
    is_approved: bool
def validate_specs(state: ExtrusionState):
    state['tolerance_check'] = True if len(state['material_spec']) > 5 else False
    return {'tolerance_check': state['tolerance_check']}
def approve_procurement(state: ExtrusionState):
    state['is_approved'] = state['tolerance_check']
    return {'is_approved': state['is_approved']}
graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()