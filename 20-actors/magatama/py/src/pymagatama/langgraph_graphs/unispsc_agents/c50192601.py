from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodState(TypedDict):
    product_name: str
    is_expired: bool
    temp_log: float
    status: str

def validate_temp(state: FoodState):
    state['status'] = 'COMPLIANT' if state['temp_log'] <= 5.0 else 'REJECTED'
    return state

def check_shelf_life(state: FoodState):
    if state['is_expired']:
        state['status'] = 'EXPIRED'
    return state

graph = StateGraph(FoodState)
graph.add_node('validate_temp', validate_temp)
graph.add_node('check_shelf_life', check_shelf_life)
graph.set_entry_point('validate_temp')
graph.add_edge('validate_temp', 'check_shelf_life')
graph.add_edge('check_shelf_life', END)

graph = graph.compile()
