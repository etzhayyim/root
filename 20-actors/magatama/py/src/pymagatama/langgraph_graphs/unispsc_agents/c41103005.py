from typing import TypedDict
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    temp_celsius: float
    capacity: int
    is_validated: bool

def validate_temp(state: FreezerState):
    state['is_validated'] = state['temp_celsius'] <= -80.0
    return 'validate_temp'

def check_capacity(state: FreezerState):
    print(f'Checking capacity for {state['capacity']} liters')
    return 'check_capacity'

graph = StateGraph(FreezerState)
graph.add_node('validate', validate_temp)
graph.add_node('capacity_check', check_capacity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'capacity_check')
graph.add_edge('capacity_check', END)
graph = graph.compile()