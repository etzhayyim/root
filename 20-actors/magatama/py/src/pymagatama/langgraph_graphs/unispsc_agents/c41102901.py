from typing import TypedDict
from langgraph.graph import StateGraph, END

class EmbeddingState(TypedDict):
    temp_setting: float
    chamber_volume: float
    is_compliant: bool

def validate_temp(state: EmbeddingState):
    state['is_compliant'] = 50 <= state['temp_setting'] <= 75
    return state

def check_capacity(state: EmbeddingState):
    if state['chamber_volume'] > 10:
        print('High capacity unit')
    return state

graph = StateGraph(EmbeddingState)
graph.add_node('validate', validate_temp)
graph.add_node('check', check_capacity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()
