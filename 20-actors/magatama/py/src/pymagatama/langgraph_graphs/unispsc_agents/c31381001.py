from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LodestoneState(TypedDict):
    magnetic_strength: float
    purity_cert: bool
    approved: bool

def validate_magnetism(state: LodestoneState):
    state['approved'] = state['magnetic_strength'] > 0.5 and state['purity_cert']
    return state

graph = StateGraph(LodestoneState)
graph.add_node('validate', validate_magnetism)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile = graph.compile()