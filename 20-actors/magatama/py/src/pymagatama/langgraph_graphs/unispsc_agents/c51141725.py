from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    storage_temp: float
    certified: bool
    approved: bool

def validate_quality(state: PharmState):
    state['approved'] = state['purity'] >= 99.0 and state['storage_temp'] <= 25.0
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()