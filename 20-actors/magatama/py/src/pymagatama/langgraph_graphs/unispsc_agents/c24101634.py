from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChainBagState(TypedDict):
    spec_data: dict
    validated: bool
    errors: List[str]

def validate_load_capacity(state: ChainBagState):
    capacity = state['spec_data'].get('load_capacity', 0)
    if capacity <= 0:
        return {'validated': False, 'errors': ['Invalid capacity']}
    return {'validated': True}

graph = StateGraph(ChainBagState)
graph.add_node('validate', validate_load_capacity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
