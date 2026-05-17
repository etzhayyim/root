from typing import TypedDict
from langgraph.graph import StateGraph, END

class AdapterState(TypedDict):
    card_type: str
    compatibility_check: bool
    is_validated: bool

def validate_adapter(state: AdapterState):
    state['is_validated'] = state['compatibility_check'] == True
    return state

graph = StateGraph(AdapterState)
graph.add_node('validate', validate_adapter)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()