from typing import TypedDict
from langgraph.graph import StateGraph, END

class DirectoryState(TypedDict):
    content_type: str
    data_accuracy: float
    distribution_points: int

def validate_data(state: DirectoryState):
    print(f'Validating accuracy: {state.get('data_accuracy', 0)}%')
    return 'validated'

def publish_directory(state: DirectoryState):
    print('Proceeding to publication/distribution phase.')
    return 'published'

graph = StateGraph(DirectoryState)
graph.add_node('validate', validate_data)
graph.add_node('publish', publish_directory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'publish')
graph.add_edge('publish', END)
app = graph.compile()