from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChainState(TypedDict):
    purity: float
    weight: float
    verified: bool

def validate_purity(state: ChainState) -> ChainState:
    state['verified'] = state['purity'] >= 0.999
    return state

def check_weight(state: ChainState) -> ChainState:
    if state['weight'] <= 0:
        raise ValueError('Invalid weight')
    return state

graph = StateGraph(ChainState)
graph.add_node('validate', validate_purity)
graph.add_node('weight_check', check_weight)
graph.add_edge('validate', 'weight_check')
graph.add_edge('weight_check', END)
graph.set_entry_point('validate')
app = graph.compile()