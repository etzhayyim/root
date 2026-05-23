from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableState(TypedDict):
    category: str
    length_meters: float
    is_compliant: bool

def validate_cable(state: CableState):
    valid_categories = ['Cat6', 'Cat6a', 'Cat7', 'Cat8']
    state['is_compliant'] = state['category'] in valid_categories and state['length_meters'] <= 100
    return state

graph = StateGraph(CableState)
graph.add_node('validate', validate_cable)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
