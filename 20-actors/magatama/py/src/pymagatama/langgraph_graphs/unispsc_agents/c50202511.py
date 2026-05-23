from typing import TypedDict
from langgraph.graph import StateGraph, END

class JuiceState(TypedDict):
    quality_score: float
    inspection_passed: bool

def check_quality(state: JuiceState):
    state['inspection_passed'] = state['quality_score'] > 0.8
    return state

graph = StateGraph(JuiceState)
graph.add_node('quality_check', check_quality)
graph.set_entry_point('quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()
