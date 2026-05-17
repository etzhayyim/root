from typing import TypedDict
from langgraph.graph import StateGraph, END

class WatermelonState(TypedDict):
    brix_level: float
    temp_log: list
    is_approved: bool

def validate_quality(state: WatermelonState):
    state['is_approved'] = state['brix_level'] >= 11.0
    return state

def check_cold_chain(state: WatermelonState):
    avg_temp = sum(state['temp_log']) / len(state['temp_log'])
    print(f'Temperature check result: {avg_temp} Celsius')
    return state

graph = StateGraph(WatermelonState)
graph.add_node('validate', validate_quality)
graph.add_node('cold_chain', check_cold_chain)
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph.set_entry_point('validate')
graph = graph.compile()