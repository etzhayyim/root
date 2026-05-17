from typing import TypedDict
from langgraph.graph import StateGraph, END

class SilverSpecState(TypedDict):
    purity: float
    weight_kg: float
    verified: bool

def validate_purity(state: SilverSpecState):
    state['verified'] = state['purity'] >= 99.9
    return state

def check_weight(state: SilverSpecState):
    print(f'Processing weight: {state['weight_kg']} kg')
    return state

graph = StateGraph(SilverSpecState)
graph.add_node('validate', validate_purity)
graph.add_node('check', check_weight)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()