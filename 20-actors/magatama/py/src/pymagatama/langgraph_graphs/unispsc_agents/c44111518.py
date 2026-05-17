from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CardHolderState(TypedDict):
    material: str
    capacity: int
    is_compliant: bool

def validate_specs(state: CardHolderState):
    # Business card holder validation logic
    state['is_compliant'] = state['capacity'] > 0 and len(state['material']) > 0
    return state

graph = StateGraph(CardHolderState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()