from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_material(state: CastingState):
    grade = state['specs'].get('grade')
    state['validated'] = grade in ['Inconel', 'Monel', 'Hastelloy']
    if not state['validated']: state['error'] = 'Invalid alloy grade for V-process'
    return state

def check_dimensions(state: CastingState):
    if state.get('validated'):
        # Logic for tolerance checking
        state['validated'] = True
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('check_dims', check_dimensions)
graph.add_edge('validate', 'check_dims')
graph.add_edge('check_dims', END)
graph.set_entry_point('validate')
graph = graph.compile()