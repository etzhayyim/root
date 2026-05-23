from typing import TypedDict
from langgraph.graph import StateGraph, END

class AmmoniaState(TypedDict):
    purity_level: float
    container_certified: bool
    compliant: bool

def validate_specs(state: AmmoniaState):
    state['compliant'] = state['purity_level'] >= 99.0 and state['container_certified']
    return state

graph = StateGraph(AmmoniaState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
