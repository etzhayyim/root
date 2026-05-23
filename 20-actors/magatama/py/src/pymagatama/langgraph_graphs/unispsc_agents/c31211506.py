from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintState(TypedDict):
    voc_content: float
    has_msds: bool
    is_approved: bool

def validate_voc(state: PaintState) -> PaintState:
    state['is_approved'] = state['voc_content'] < 50.0
    return state

def check_documentation(state: PaintState) -> PaintState:
    state['is_approved'] = state['is_approved'] and state['has_msds']
    return state

graph = StateGraph(PaintState)
graph.add_node('validate_voc', validate_voc)
graph.add_node('check_docs', check_documentation)
graph.set_entry_point('validate_voc')
graph.add_edge('validate_voc', 'check_docs')
graph.add_edge('check_docs', END)
graph = graph.compile()
