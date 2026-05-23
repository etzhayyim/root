from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_bearing(state: BearingState):
    specs = state['spec_data']
    if 'bore_diameter' in specs and 'load_rating_dynamic' in specs:
        return {'validated': True}
    return {'validated': False, 'error': 'Missing critical technical specs'}

def approval_step(state: BearingState):
    return {'validated': True}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_bearing)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
