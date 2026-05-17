from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MediaGraphState(TypedDict):
    batch_id: str
    is_sterile: bool
    ph_value: float
    qc_passed: bool

def validate_media(state: MediaGraphState) -> MediaGraphState:
    # Logic for Dictyostelium media quality assurance
    state['qc_passed'] = state['is_sterile'] and (6.5 <= state['ph_value'] <= 7.0)
    return state

graph = StateGraph(MediaGraphState)
graph.add_node('validate', validate_media)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()