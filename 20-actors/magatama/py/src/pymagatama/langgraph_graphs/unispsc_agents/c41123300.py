from typing import TypedDict
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    spec_data: dict
    validated: bool

def validate_safety_compliance(state: StorageState):
    # Logic to check fire rating and chemical compatibility
    state['validated'] = state['spec_data'].get('fire_rating') is not None
    return state

def route_verification(state: StorageState):
    return 'verified' if state['validated'] else 'rejected'

graph = StateGraph(StorageState)
graph.add_node('validator', validate_safety_compliance)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
compiled_graph = graph.compile()