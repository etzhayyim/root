from typing import TypedDict
from langgraph.graph import StateGraph, END
class ResourceState(TypedDict):
    isbn: str
    is_valid: bool
    metadata: dict
def validate_isbn(state: ResourceState):
    state['is_valid'] = len(state['isbn']) in [10, 13]
    return state
def classify_resource(state: ResourceState):
    state['metadata'] = {'type': 'verb_dictionary', 'status': 'processed'}
    return state
graph = StateGraph(ResourceState)
graph.add_node('validate', validate_isbn)
graph.add_node('classify', classify_resource)
graph.add_edge('validate', 'classify')
graph.add_edge('classify', END)
graph.set_entry_point('validate')
graph = graph.compile()