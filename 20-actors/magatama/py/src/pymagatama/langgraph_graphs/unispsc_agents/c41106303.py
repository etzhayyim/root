from typing import TypedDict
from langgraph.graph import StateGraph, END

class PCRState(TypedDict):
    purity_level: float
    storage_temp: float
    is_validated: bool

def validate_temp(state: PCRState):
    state['is_validated'] = state['storage_temp'] <= -20.0
    return state

def check_quality(state: PCRState):
    if state['purity_level'] >= 0.95:
        return 'ready'
    return 'retest'

graph = StateGraph(PCRState)
graph.add_node('validate', validate_temp)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()