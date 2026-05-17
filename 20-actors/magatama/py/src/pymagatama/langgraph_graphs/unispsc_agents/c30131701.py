from typing import TypedDict
from langgraph.graph import StateGraph, END

class TileState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: TileState):
    required = ['compressive_strength', 'water_absorption']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def check_durability(state: TileState):
    if state['approved'] and state['specs']['compressive_strength'] > 30:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(TileState)
graph.add_node('validate', validate_specs)
graph.add_node('durability', check_durability)
graph.add_edge('validate', 'durability')
graph.add_edge('durability', END)
graph.set_entry_point('validate')
graph = graph.compile()