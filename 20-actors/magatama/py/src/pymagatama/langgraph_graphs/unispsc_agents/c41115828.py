from typing import TypedDict
from langgraph.graph import StateGraph, END

class UrinalysisState(TypedDict):
    item_name: str
    ivd_certified: bool
    temp_control: bool
    validated: bool

def validate_consumables(state: UrinalysisState):
    state['validated'] = state['ivd_certified'] and state['temp_control']
    return state

graph = StateGraph(UrinalysisState)
graph.add_node('validate', validate_consumables)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
