from typing import TypedDict
from langgraph.graph import StateGraph, END

class PetriState(TypedDict):
    diameter: float
    sterility_confirmed: bool
    is_compliant: bool

def validate_specs(state: PetriState):
    state['is_compliant'] = state['diameter'] > 0 and state['sterility_confirmed']
    return state

graph = StateGraph(PetriState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()