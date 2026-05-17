from typing import TypedDict
from langgraph.graph import StateGraph, END

class RemovalKitState(TypedDict):
    material_type: str
    solvent_grade: str
    is_safe: bool

def validate_solvent(state: RemovalKitState):
    state['is_safe'] = state['solvent_grade'] == 'industrial-compliant'
    return state

def check_compatibility(state: RemovalKitState):
    if state['material_type'] == 'plastic' and not state['is_safe']:
        print('Compatibility risk identified')
    return state

graph = StateGraph(RemovalKitState)
graph.add_node('validate', validate_solvent)
graph.add_node('compatible', check_compatibility)
graph.add_edge('validate', 'compatible')
graph.add_edge('compatible', END)
graph.set_entry_point('validate')
graph = graph.compile()