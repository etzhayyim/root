from typing import TypedDict
from langgraph.graph import StateGraph, END

class StampAlbumState(TypedDict):
    material_spec: str
    is_archival: bool
    validation_score: int

def validate_materials(state: StampAlbumState) -> StampAlbumState:
    state['is_archival'] = 'acid-free' in state['material_spec'].lower()
    state['validation_score'] = 10 if state['is_archival'] else 0
    return state

def check_quality(state: StampAlbumState) -> str:
    return 'VALID' if state['validation_score'] > 0 else 'INVALID'

graph = StateGraph(StampAlbumState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
