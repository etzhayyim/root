from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PureeState(TypedDict):
    purity_level: float
    bacterial_count: int
    is_approved: bool

def validate_quality(state: PureeState):
    if state['bacterial_count'] < 1000 and state['purity_level'] > 0.95:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(PureeState)
graph.add_node('validation', validate_quality)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()