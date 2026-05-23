from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoathookState(TypedDict):
    material: str
    length: float
    inspection_passed: bool

def validate_material(state: BoathookState):
    state['inspection_passed'] = state['material'] in ['Aluminum', 'Fiberglass', 'Stainless Steel']
    return state

def check_length(state: BoathookState):
    state['inspection_passed'] = state['inspection_passed'] and (state['length'] > 0)
    return state

graph = StateGraph(BoathookState)
graph.add_node('validate_mat', validate_material)
graph.add_node('check_len', check_length)
graph.set_entry_point('validate_mat')
graph.add_edge('validate_mat', 'check_len')
graph.add_edge('check_len', END)
app = graph.compile()
