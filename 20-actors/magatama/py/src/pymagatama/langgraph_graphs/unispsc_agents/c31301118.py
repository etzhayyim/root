from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_material(state: ForgingState):
    grade = state['specs'].get('grade')
    state['validated'] = grade is not None and len(grade) > 0
    return state

def check_quality(state: ForgingState):
    if not state.get('validated'):
        state['error'] = 'Invalid Metallurgy Spec'
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_material)
graph.add_node('quality', check_quality)
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph.set_entry_point('validate')
graph = graph.compile()