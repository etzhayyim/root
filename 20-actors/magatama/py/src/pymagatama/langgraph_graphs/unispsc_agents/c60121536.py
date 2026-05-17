from langgraph.graph import StateGraph, END
from typing import TypedDict

class CleaningTaskState(TypedDict):
    surface_type: str
    material_tested: bool
    safety_approved: bool

def validate_surface(state: CleaningTaskState):
    state['material_tested'] = state['surface_type'] in ['painted_wall', 'tile', 'hardwood']
    return state

def check_safety(state: CleaningTaskState):
    state['safety_approved'] = True
    return state

graph = StateGraph(CleaningTaskState)
graph.add_node('validate', validate_surface)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()