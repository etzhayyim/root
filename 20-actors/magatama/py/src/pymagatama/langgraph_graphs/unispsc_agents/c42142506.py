from typing import TypedDict
from langgraph.graph import StateGraph, END

class NeedleState(TypedDict):
    gauge: float
    sterile: bool
    approved: bool

def validate_spec(state: NeedleState):
    state['approved'] = state['gauge'] > 0 and state['sterile']
    return state

graph = StateGraph(NeedleState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
