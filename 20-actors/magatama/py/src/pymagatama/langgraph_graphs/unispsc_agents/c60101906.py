from typing import TypedDict
from langgraph.graph import StateGraph, END

class PosterState(TypedDict):
    spec_data: dict
    approved: bool

def validate_materials(state: PosterState):
    # Basic validation logic for educational safety standards
    state['approved'] = state['spec_data'].get('safety_cert') == 'EN71'
    return state

graph = StateGraph(PosterState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()