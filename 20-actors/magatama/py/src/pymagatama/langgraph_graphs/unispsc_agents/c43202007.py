from typing import TypedDict
from langgraph.graph import StateGraph, END

class DataStorageState(TypedDict):
    media_type: str
    capacity: int
    is_verified: bool

def validate_media_spec(state: DataStorageState):
    # Simulate CAD/Spec validation logic for storage media
    state['is_verified'] = state['capacity'] > 0
    return state

def storage_workflow(state: DataStorageState):
    print(f'Processing {state["media_type"]} with capacity {state["capacity"]}GB')
    return {'is_verified': True}

graph = StateGraph(DataStorageState)
graph.add_node('validate', validate_media_spec)
graph.add_node('process', storage_workflow)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
