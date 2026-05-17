from typing import TypedDict
from langgraph.graph import StateGraph, END

class DataState(TypedDict):
    spec: dict
    validated: bool

def validate_cross_connect(state: DataState):
    # Perform compatibility check for cable and port standards
    state['validated'] = state['spec'].get('standard') == 'TIA-568'
    return state

graph = StateGraph(DataState)
graph.add_node('validate', validate_cross_connect)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()