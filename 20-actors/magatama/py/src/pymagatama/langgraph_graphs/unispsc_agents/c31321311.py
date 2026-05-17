from langgraph.graph import StateGraph, END
from typing import TypedDict
class ProcurementState(TypedDict):
    material_spec: str
    inspection_passed: bool
    compliant: bool
def validate_material(state: ProcurementState):
    state['compliant'] = state['material_spec'] == 'Waspalloy-AMS' 
    return state
def check_quality(state: ProcurementState):
    state['inspection_passed'] = state['compliant']
    return state
graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', check_quality)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()