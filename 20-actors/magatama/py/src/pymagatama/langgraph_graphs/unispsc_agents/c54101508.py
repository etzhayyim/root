from typing import TypedDict
from langgraph.graph import StateGraph, END

class JewelryState(TypedDict):
    item_id: str
    purity_certified: bool
    value: float
    inspection_passed: bool

def verify_purity(state: JewelryState):
    state['purity_certified'] = True
    return state

def evaluate_value(state: JewelryState):
    state['inspection_passed'] = state['value'] > 0
    return state

graph = StateGraph(JewelryState)
graph.add_node('verify', verify_purity)
graph.add_node('evaluate', evaluate_value)
graph.add_edge('verify', 'evaluate')
graph.add_edge('evaluate', END)
graph.set_entry_point('verify')
app = graph.compile()
