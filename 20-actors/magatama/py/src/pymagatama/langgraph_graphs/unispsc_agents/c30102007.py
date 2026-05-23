from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    purity: float
    thickness: float
    hazmat_clearance: bool

def validate_purity(state: MagnesiumState):
    if state['purity'] < 99.9:
        print('Warning: Purity below industrial standards.')
    return 'validated'

def check_hazmat(state: MagnesiumState):
    if state['thickness'] < 0.1:
        print('Flash fire risk detected: Special storage required.')
    return 'safe_to_process'

graph = StateGraph(MagnesiumState)
graph.add_node('validate', validate_purity)
graph.add_node('hazmat_check', check_hazmat)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazmat_check')
graph.add_edge('hazmat_check', END)
graph = graph.compile()
