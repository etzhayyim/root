from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PlasticState(TypedDict):
    material_name: str
    softening_temp: float
    safety_checked: bool
    approved: bool

def validate_material(state: PlasticState):
    state['safety_checked'] = state['softening_temp'] < 100
    return {'safety_checked': state['safety_checked']}

def approval_logic(state: PlasticState):
    state['approved'] = state['safety_checked']
    return {'approved': state['approved']}

graph = StateGraph(PlasticState)
graph.add_node('validate', validate_material)
graph.add_node('approve', approval_logic)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
