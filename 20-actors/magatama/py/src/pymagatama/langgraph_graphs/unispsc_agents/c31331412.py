from typing import TypedDict
from langgraph.graph import StateGraph, END
class AssemblyState(TypedDict):
    material_spec: dict
    uv_integrity_check: bool
    approved: bool
def validate_welding(state: AssemblyState):
    state['uv_integrity_check'] = state['material_spec'].get('depth', 0) > 0.5
    return {'uv_integrity_check': state['uv_integrity_check']}
def final_check(state: AssemblyState):
    state['approved'] = state['uv_integrity_check']
    return {'approved': state['approved']}
graph = StateGraph(AssemblyState)
graph.add_node('val_weld', validate_welding)
graph.add_node('final', final_check)
graph.add_edge('val_weld', 'final')
graph.add_edge('final', END)
graph.set_entry_point('val_weld')
graph = graph.compile()
