from typing import TypedDict
from langgraph.graph import StateGraph, END

class ResourceState(TypedDict):
    isbn: str
    is_verified: bool
    is_current_edition: bool

def validate_isbn(state: ResourceState):
    state['is_verified'] = len(state['isbn']) >= 10
    return state

def check_edition(state: ResourceState):
    state['is_current_edition'] = True
    return state

graph = StateGraph(ResourceState)
graph.add_node('validate', validate_isbn)
graph.add_node('edition_check', check_edition)
graph.set_entry_point('validate')
graph.add_edge('validate', 'edition_check')
graph.add_edge('edition_check', END)
app = graph.compile()
