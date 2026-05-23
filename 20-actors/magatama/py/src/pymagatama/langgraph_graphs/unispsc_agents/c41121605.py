from typing import TypedDict
from langgraph.graph import StateGraph, END

class TipState(TypedDict):
    brand: str
    volume_ul: float
    purity_level: str
    is_validated: bool

def validate_spec(state: TipState):
    if state['volume_ul'] < 0.1 or state['volume_ul'] > 20:
        return {'is_validated': False}
    return {'is_validated': True}

def check_purity(state: TipState):
    required_levels = ['RNase-free', 'DNase-free', 'Pyrogen-free']
    return {'is_validated': state['purity_level'] in required_levels}

graph = StateGraph(TipState)
graph.add_node('validate_spec', validate_spec)
graph.add_node('check_purity', check_purity)
graph.set_entry_point('validate_spec')
graph.add_edge('validate_spec', 'check_purity')
graph.add_edge('check_purity', END)
graph = graph.compile()
