from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec_data: dict
    validated: bool

def validate_bearing(state: BearingState):
    required = ['Load Rating', 'Material']
    return {'validated': all(k in state['spec_data'] for k in required)}

def finalize_order(state: BearingState):
    print('Procurement logic for bearings finalized.')

graph = StateGraph(BearingState)
graph.add_node('validate', validate_bearing)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()