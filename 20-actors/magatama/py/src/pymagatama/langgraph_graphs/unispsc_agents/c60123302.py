from typing import TypedDict
from langgraph.graph import StateGraph, END

class CraftState(TypedDict):
    material: str
    quality_score: float
    glitter_retention: bool

def validate_materials(state: CraftState):
    state['quality_score'] = 1.0 if 'non-toxic' in state['material'] else 0.5
    return state

def check_adhesion(state: CraftState):
    state['glitter_retention'] = True
    return state

graph = StateGraph(CraftState)
graph.add_node('validate', validate_materials)
graph.add_node('adhesion', check_adhesion)
graph.set_entry_point('validate')
graph.add_edge('validate', 'adhesion')
graph.add_edge('adhesion', END)
graph = graph.compile()