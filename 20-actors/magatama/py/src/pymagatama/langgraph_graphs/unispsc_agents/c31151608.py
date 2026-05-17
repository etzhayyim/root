from langgraph.graph import StateGraph, END
from typing import TypedDict

class ChainState(TypedDict):
    material: str
    diameter: float
     tensile_strength: float
    is_compliant: bool

def validate_ball_chain(state: ChainState):
    # Business logic for confirming ballistic/jewelry grade specs
    state['is_compliant'] = state['diameter'] > 0 and state['tensile_strength'] > 50
    return state

graph = StateGraph(ChainState)
graph.add_node('validate', validate_ball_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()