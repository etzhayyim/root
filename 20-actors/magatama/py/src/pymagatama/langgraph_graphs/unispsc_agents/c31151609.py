from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChainState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_load_capacity(state: ChainState):
    capacity = state['spec_data'].get('load_capacity', 0)
    valid = capacity > 0
    return {'validated': valid, 'error_log': [] if valid else ['Capacity <= 0']}

def finalize_order(state: ChainState):
    return {'validated': True}

graph = StateGraph(ChainState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)

app = graph.compile()