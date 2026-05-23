from typing import TypedDict
from langgraph.graph import StateGraph, END

class StandState(TypedDict):
    load_capacity: float
    material: str
    is_stable: bool

def validate_load(state: StandState):
    state['is_stable'] = state['load_capacity'] > 0
    return state

def finalize_spec(state: StandState):
    return state

graph = StateGraph(StandState)
graph.add_node('validate', validate_load)
graph.add_node('finalize', finalize_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
