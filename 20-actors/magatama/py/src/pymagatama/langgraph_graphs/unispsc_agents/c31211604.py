from langgraph.graph import StateGraph, END
from typing import TypedDict
class PaintExtenderState(TypedDict):
    material_name: str
    purity_level: float
    safety_check_passed: bool
    approved: bool
def validate_material(state: PaintExtenderState):
    state['safety_check_passed'] = state['purity_level'] >= 95.0
    return state
def approval_step(state: PaintExtenderState):
    state['approved'] = state['safety_check_passed']
    return state
graph = StateGraph(PaintExtenderState)
graph.add_node('validate', validate_material)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
