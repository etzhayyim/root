from typing import TypedDict
from langgraph.graph import StateGraph, END

class PreciousMetalState(TypedDict):
    purity: float
    weight: float
    verified: bool

def validate_purity(state: PreciousMetalState):
    state['verified'] = state['purity'] >= 0.999
    return state

def check_weight(state: PreciousMetalState):
    print(f'Checking weight for: {state.get('weight', 0)}g')
    return state

graph = StateGraph(PreciousMetalState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_weight', check_weight)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_weight')
graph.add_edge('check_weight', END)
graph = graph.compile()