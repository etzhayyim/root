from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CookiePressState(TypedDict):
    material_safety: bool
    nozzle_count: int
    is_validated: bool

def check_food_safety(state: CookiePressState):
    state['is_validated'] = state['material_safety'] is True and state['nozzle_count'] > 0
    return state

graph = StateGraph(CookiePressState)
graph.add_node('validate', check_food_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
