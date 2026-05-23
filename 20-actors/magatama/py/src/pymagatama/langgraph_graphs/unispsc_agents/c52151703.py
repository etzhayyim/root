from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForkState(TypedDict):
    material_certified: bool
    safety_checked: bool
    finished: bool

def validate_material(state: ForkState):
    state['material_certified'] = True
    return 'check_safety'

def check_safety(state: ForkState):
    state['safety_checked'] = True
    state['finished'] = True
    return END

graph = StateGraph(ForkState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_safety', check_safety)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()
