from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProjectState(TypedDict):
    materials: List[str]
    validation_score: float
    approved: bool

def validate_materials(state: ProjectState) -> ProjectState:
    state['validation_score'] = 1.0 if len(state['materials']) > 0 else 0.0
    state['approved'] = state['validation_score'] > 0.5
    return state

graph = StateGraph(ProjectState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()