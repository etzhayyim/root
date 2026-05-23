from typing import TypedDict
from langgraph.graph import StateGraph, END

class PhospholipidState(TypedDict):
    purity: float
    storage_temp: float
    is_validated: bool

def check_purity(state: PhospholipidState):
    state['is_validated'] = state['purity'] >= 98.0
    return state

def check_temp(state: PhospholipidState):
    state['is_validated'] = state['is_validated'] and (-20 <= state['storage_temp'] <= 4)
    return state

graph = StateGraph(PhospholipidState)
graph.add_node('check_purity', check_purity)
graph.add_node('check_temp', check_temp)
graph.set_entry_point('check_purity')
graph.add_edge('check_purity', 'check_temp')
graph.add_edge('check_temp', END)
graph = graph.compile()
